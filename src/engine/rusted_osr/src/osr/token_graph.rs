use std::collections::{BTreeMap, HashMap, HashSet};
use std::hash::RandomState;
use petgraph::{Graph, Undirected};
use petgraph::algo::all_simple_paths;
use petgraph::graph::{NodeIndex, UnGraph};
use rusted_engine::api::dex::snapshot::TokenData;
use rusted_soul_dex::dex::metadata::{Metadata, Path};
use crate::config::{INTERMEDIATE_BASES, SUPPORTED_NETWORK_LIST};
use crate::errors::SoulOsrError;

pub struct TokensGraph {
    pub network: String,
    pub graph: Graph<String, Vec<String>, Undirected>,
    pub tokens: HashMap<String, TokenData>,
    map: HashMap<String, NodeIndex>,
}

impl TokensGraph {
    pub fn new(
        metadata: &BTreeMap<String, Metadata>,
        network: String
    ) -> Result<Self, SoulOsrError>  {
        if !SUPPORTED_NETWORK_LIST.contains(&network.as_str()) {
            return Err(SoulOsrError::NotSupportedNetwork);
        }

        let mut graph = UnGraph::<String, Vec<String>>::new_undirected();
        let mut map: HashMap<String, NodeIndex> = HashMap::new();
        let mut tokens: HashMap<String, TokenData> = HashMap::new();

        for (pool, data) in metadata {
            let a = &data.mint0;
            let b = &data.mint1;

            tokens.entry(a.clone()).or_insert_with(|| TokenData { decimals: data.decimals0 as u32 });
            tokens.entry(b.clone()).or_insert_with(|| TokenData { decimals: data.decimals1 as u32 });

            let a_idx = *map.entry(a.clone())
                .or_insert_with(|| graph.add_node(a.clone()));
            let b_idx = *map.entry(b.clone())
                .or_insert_with(|| graph.add_node(b.clone()));

            let edge = match graph.find_edge(a_idx, b_idx) {
                Some(e) => e,
                None => graph.add_edge(a_idx, b_idx, Vec::new()),
            };

            graph[edge].push(pool.clone());
        }

        Ok(Self { network, graph, tokens, map })
    }


    // This function gives filtered paths from all possible paths from token A to token B (3 hopes)
    pub fn get_filtered_paths(
        &self,
        from: &String,
        to: &String
    ) -> Result<Vec<Path>, SoulOsrError> {
        if !SUPPORTED_NETWORK_LIST.contains(&self.network.as_str()) {
            return Err(SoulOsrError::NotSupportedNetwork);
        }

        let node_idx_from = self.map
            .get(from)
            .ok_or(SoulOsrError::ThisTokenWasNotFoundInNodes)?
            .clone();
        let node_idx_to = self.map.
            get(to).
            ok_or(SoulOsrError::ThisTokenWasNotFoundInNodes)?
            .clone();

        let intermediate_nodes: HashSet<NodeIndex> = {
            let mut res: HashSet<NodeIndex> = HashSet::new();

            let intermediate_bases = INTERMEDIATE_BASES
                .get(self.network.as_str())
                .ok_or(SoulOsrError::NotSupportedNetwork)?;

            for base in intermediate_bases {
                if let Some(node) = self.map.get(&base.to_string()) {
                    res.insert(node.clone());
                }
            }

            res
        };

        let filtered_node_paths: Vec<Vec<NodeIndex>> = {
            let mut res: Vec<Vec<NodeIndex>> = Vec::new();

            let dirty_paths: Vec<Vec<NodeIndex>> = all_simple_paths::<Vec<_>, _, RandomState>(
                &self.graph,
                node_idx_from,
                node_idx_to,
                0,
                Some(2)
            ).collect();

            'path_loop: for path in dirty_paths {
                'node_loop: for node in path.iter() {
                    if node == &node_idx_from || node == &node_idx_to {
                        continue 'node_loop;
                    } else if !intermediate_nodes.contains(&node){
                        continue 'path_loop;
                    }
                }

                res.push(path);
            }

            res
        };

        Ok(self.resolve_node_path_to_pool_path(filtered_node_paths))
    }


    // This function gives all possible paths from token A to token B (n hopes)
    pub fn get_all_paths(
        &self,
        from: &String,
        to: &String,
        max_intermediate_nodes: Option<usize>,
    ) -> Result<Vec<Path>, SoulOsrError> {
        if !SUPPORTED_NETWORK_LIST.contains(&self.network.as_str()) {
            return Err(SoulOsrError::NotSupportedNetwork);
        }

        let node_idx_from = self.map
            .get(from)
            .ok_or(SoulOsrError::ThisTokenWasNotFoundInNodes)?
            .clone();
        let node_idx_to = self.map.
            get(to).
            ok_or(SoulOsrError::ThisTokenWasNotFoundInNodes)?
            .clone();

        let all_possible_node_paths: Vec<Vec<NodeIndex>> = all_simple_paths::<Vec<_>, _, RandomState>(
            &self.graph,
            node_idx_from,
            node_idx_to,
            0,
            max_intermediate_nodes
        ).collect();

        Ok(self.resolve_node_path_to_pool_path(all_possible_node_paths))
    }

    fn resolve_node_path_to_pool_path(
        &self,
        node_paths: Vec<Vec<NodeIndex>>
    ) -> Vec<Path> {
        let mut pool_paths: Vec<Path> = Vec::new();

        'node_path_loop: for node_path in node_paths {
            let mut edge_paths: Vec<Path> = vec![vec![]];

            for i in 0..(node_path.len() - 1) {
                let node_a = node_path[i];
                let node_b = node_path[i+1];

                let edge: Path = match self.graph.find_edge(node_a, node_b) {
                    Some(e) => {self.graph[e].clone()},
                    None => continue 'node_path_loop,
                };

                let mut new_edge_paths: Vec<Path> = Vec::new();

                for path in edge_paths.iter() {
                    for pool in edge.iter() {
                        let mut new_path = path.clone();
                        new_path.push(pool.clone());

                        new_edge_paths.push(new_path);
                    }
                }

                edge_paths = new_edge_paths;
            }

            pool_paths.extend(edge_paths);
        }

        pool_paths
    }
}
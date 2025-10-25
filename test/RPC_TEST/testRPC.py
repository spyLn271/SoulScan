from src.DEX.DEX_RPC.toolsKit.Solana import Solana
import json


async def main():
    async with Solana() as solana:
        addresses = ['Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE',
                     '7XFiNgEcwiUUKw4GadjHv87kGSef3RKqh4TYmnkErtmB',
                     ]
        dlmm_address = ['5hbf9JP8k5zdrZp9pokPypFQoBse5mGCmW6nqodurGcd',
                        '8ztFxjFPfVUtEf4SLSapcFj8GW2dxyUA9no2bLPq7H7V']
        #
        # target_idl_name = 'Tick'
        #
        # structure = solana.getStruct(idl=solana.idls.get('orca'),
        #                              target_name=target_idl_name,
        #                              definition=solana.definition.get('orca'),
        #                              merging=solana.merging.get('orca'))
        #
        # print(structure.subcons)


        fields = ['data']
        funcs = {'data': lambda x: solana.translate(x[0], 'Whirlpool', 'orca')}
        data = await solana.getMultipleAccounts(addresses, field=fields, funcs=funcs)
        print(json.dumps(data, indent=4))

        dlmm_funcs = {'data': lambda x: solana.translate(x[0], 'LbPair', 'dlmm')}
        dlmm_data = await solana.getMultipleAccounts(dlmm_address, field=fields, funcs=dlmm_funcs)
        print(json.dumps(dlmm_data, indent=4))


        # res = await solana.getMultipleSPLAccountsBalance(['CoaxzEh8p5YyGLcj36Eo3cUThVJxeKCs7qvLAGDYwBcz',
        #                                                'EYj9xKw6ZszwpyNibHY7JD5o3QgTVrSdcBp1fMJhrR9o'])
        # print(json.dumps(res, indent=4))




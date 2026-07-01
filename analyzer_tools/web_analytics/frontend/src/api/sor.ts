export interface GetQuote {
  network: string
  address0: string
  address1: string
  amount: bigint // u128 on the backend
  a_to_b: boolean
  amount_specified_is_in: boolean
}

export const SOR_ENDPOINT = '/v1/sor'

export const U128_MAX = (1n << 128n) - 1n

export function serializeGetQuote(q: GetQuote): string {
  return (
    '{' +
    `"network":${JSON.stringify(q.network)},` +
    `"address0":${JSON.stringify(q.address0)},` +
    `"address1":${JSON.stringify(q.address1)},` +
    `"amount":${q.amount.toString()},` +
    `"a_to_b":${q.a_to_b},` +
    `"amount_specified_is_in":${q.amount_specified_is_in}` +
    '}'
  )
}

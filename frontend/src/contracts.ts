/**
 * Contract access for the UI. Types are generated from the canonical backend models;
 * `validateContract` checks mocks and responses against the same JSON Schema at runtime,
 * because a TypeScript type alone is not validation (decision 0001).
 */
import Ajv2020, { type ValidateFunction } from 'ajv/dist/2020'
import schema from '../../contracts/schema/crisis-command.schema.json'

export type * from './generated/contracts'

export const CONTRACT_SCHEMA_VERSION = '1.0'

const ajv = new Ajv2020({ allErrors: true, strict: false })
ajv.addSchema(schema, 'contracts')

const cache = new Map<string, ValidateFunction>()

export type ContractName = keyof typeof schema.$defs

export interface ContractCheck {
  valid: boolean
  errors: string[]
}

export function validateContract(name: ContractName, value: unknown): ContractCheck {
  let validate = cache.get(name)
  if (!validate) {
    validate = ajv.compile({ $ref: `contracts#/$defs/${name}` })
    cache.set(name, validate)
  }
  const valid = validate(value)
  return {
    valid,
    errors: valid ? [] : (validate.errors ?? []).map((e) => `${e.instancePath || '/'} ${e.message ?? ''}`),
  }
}

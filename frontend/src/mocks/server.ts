import { setupServer } from 'msw/node'
import { handlers } from './handlers'

/** MSW server for Vitest tests — call server.listen() / server.close() in setup */
export const server = setupServer(...handlers)

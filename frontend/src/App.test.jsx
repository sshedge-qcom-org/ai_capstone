import { render, screen, cleanup } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, expect, test } from 'vitest'
import { Landing } from './App'

afterEach(cleanup)
test('landing offers workspace entry', () => {
  render(<MemoryRouter><Landing /></MemoryRouter>)
  expect(screen.getByRole('link', { name: 'Enter your workspace' }).getAttribute('href')).toBe('/login')
})

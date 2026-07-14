# Web app local rules

- Follow root `AGENTS.md` and contracts.
- Mobile-first: verify 390px and 430px; no horizontal overflow.
- Use semantic HTML, keyboard operation, visible focus, modal focus trap/return.
- Body contrast >= 4.5:1 and do not encode status by color only.
- Render source metadata exactly as returned by API; never invent or rewrite URLs/dates.
- Display official/event/evaluation/mock badges clearly.
- Pages remain `/`, `/chat`, `/admin`; use tabs/cards/modals instead of new pages unless human approves.
- P2 UI should not be silently added.
- Keep API calls in a typed client generated/aligned from contracts.
- Add component/E2E tests for every user-visible state.

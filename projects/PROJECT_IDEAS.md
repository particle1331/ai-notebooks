# Project Ideas

Notebook and app ideas to revisit later.

---

## `notebooks/apps/cda/` — Coding Agent UI

### Multi-user agent sessions (`08-ui4.ipynb`)

Share a running agent session across multiple connected users via Flet's `page.pubsub`.

**Concept:**
- Each browser tab / desktop window is an isolated Flet `page` (Flet already handles this)
- One user is the "host" — their page owns the agent loop and drives `agent.run()`
- Agent events (text deltas, tool calls, approvals) are broadcast to all subscribers via `page.pubsub`
- All connected users see the feed update live
- Any user can trigger an approval decision (or restrict it to the host)
- Status bar shows connected user count alongside turn / token stats

**Key design decision:** host model (one agent, many observers) is simpler than a turn-based model where any user can send messages. Start with host model.

**Relevant prior art:** `notebooks/apps/03-flet.ipynb` covers PubSub-based chatroom as a worked example — the broadcast pattern is the same.

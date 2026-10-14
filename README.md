# Monster Roommates

A cozy logic puzzle for phones, in one HTML file. Monsters are moving into a crooked little house, and
every house comes with house rules, such as: the vampire wants no moonlight, the ghost lives in the
attic, the spider wants no neighbours, the bat must be next to the witch. Move everyone in so that every rule is
green. Break one and the house goes **BUMP!**

- **Houses:** a grid of rooms. The top row is the attic, the bottom row the cellar, and some rooms have
  a moonlit pane. "Next to" means the rooms share a wall.
- **Rules:** needs moonlight / no moonlight, attic, cellar, no neighbours, needs a neighbour, next to,
  not next to, upstairs of, same floor as, left of. They are taught one kind at a time.
- **Exactly one answer:** every house is grown from a seed. The generator picks rooms, tenants and an
  answer, adds rules that are true of that answer until a solver proves it is the only one, then takes
  out every rule that isn't needed. No house is kept until the solver has proved it has one answer.
- **The street:** houses grow from 2 x 2 with three tenants up to 4 x 3 with eight, and a new tenant moves
  in every third house (ten in all). Up to 3 stars per house: no hints, and at most two moves more than
  there are tenants. Every third house earns a hint.
- **Daily House:** one 3 x 3 house a day, the same for everyone, with a streak and a score.

Made for RUN's October Jam ("Monster Mash": "monsters as the hero, the villain, the roommate").
Made by MV2 of Munim, Inc. with AI agents (Anthropic Claude): the code, art and sound are all AI-made,
and there are no premade assets. The house is drawn in code, the tenants are emoji, and the sound is
synthesized in the browser.

## On RUN

RUN's game frame has no `localStorage`, so the RUN build loads RUN's SDK before the game
(`window.RundotGameAPI`). When it is there, the game:

- saves the street to the player's RUN storage (`appStorage`), and waits up to 4 seconds for it on start;
- adds a **Share** button when a house is done: the link carries that house and your number of moves, and
  a friend who opens it gets the same house, sees your moves to beat, and earns a hint for finishing it;
- sends each first Daily House result of the day to RUN's **leaderboard** (higher is better: 1000, minus
  25 for each move over the number of tenants, 100 for each hint and 1 a second up to 300);
- offers an **optional rewarded ad** for two hints, only when the hints have run out and RUN says an ad is
  ready;
- after the Daily House, schedules a **local reminder** for 6 pm the next day.

Every SDK call is wrapped so that a failure can't stop the game. Anywhere else (a plain browser, itch.io)
none of this appears and progress is saved in the browser.

`build_run.mjs` makes the RUN build: `npm install`, then `node build_run.mjs run-dist` writes
`run-dist/dist` (deploy that folder with `rundot deploy`) and `run-dist/build-report.json`. RUN's SDK
(`@series-inc/rundot-game-sdk`) is not part of this repository and keeps its own licence.

## Play and check

- Open `index.html` in a browser. Portrait, 720 x 1280, letterboxed on wider screens.
- Controls: tap a monster, then a room. Tap a room's tenant to move it; moving into an occupied room swaps
  the two. Tap a tenant's card twice to send it back to the doorstep. Keys: 1-8 pick a tenant, Escape lets
  go, H hint, R restart, D Daily House, Enter next house, M sound on or off.
- `index.html#selftest` checks the rules and the solver, then plays sixteen houses, a swap, hints, the
  Daily House and a friend's house through the real code and lists any problems.
- `index.html#demo` moves tenants in by itself (for videos); it never saves.
- `index.html#cover` draws the covers (1024 x 1024, 720 x 1280, 1280 x 720).

## Tests

    python -m unittest -v test_monster_roommates.py

Static checks always run, including that every RUN SDK call goes through the guard. With Node.js installed,
the rules block must pass its own checks: the solver counts known small cases correctly, houses 1-36 and ten
Daily Houses each have exactly one answer (re-proved with a large search budget), use only rules already
taught, include each new tenant, and come out the same every time. The whole page runs against a stub
browser: houses played with clicks and keys, a broken rule going bump, hints, restart, the Daily House, a new
tenant, a phone-shaped window, and a session on RUN with a fake SDK (the saved street loads, a friend's link
opens their house, the ad gives hints, Share, the leaderboard and the reminder).

## Licence

Apache-2.0. Copyright 2026 Munim, Inc.

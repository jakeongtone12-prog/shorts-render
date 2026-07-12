# shorts-render — START HERE

CI render farm for Unscramble Your Life Shorts. Free forever: GitHub Actions renders the videos, this repo hosts them, Claude publishes them to YouTube via Zapier. No credentials ever pass through the AI.

## Activate (one time, ~30 seconds)
GitHub's API blocks bots from installing workflows, so this last step is yours:

1. Open `SETUP-render.yml` in this repo
2. Click the pencil (edit) icon
3. In the filename box, change `SETUP-render.yml` to `.github/workflows/render.yml`
4. Commit

That commit triggers the first run: all 6 videos (pilot + 5 queued scripts) render in ~15 min and appear in `out/`.

## Then tell Claude
Say **"renders are done"** in the chat. Claude verifies `out/`, then publishes approved videos to YouTube by passing the raw file URLs to Zapier — e.g. `https://raw.githubusercontent.com/jakeongtone12-prog/shorts-render/main/out/pilot.mp4`.

## Daily operation after that
1. Ask Claude for a new script → Claude commits `scripts/NN-topic.json` here
2. CI renders it automatically on push
3. Claude publishes it with your go-ahead

Scene format: `{"scenes": [["text", seconds, accent_color_0_to_5], ...]}`

# Say It Like Steve

I trained my own AI model that turns my speech scripts into the way Steve Jobs would say them.

English is my second language, and speaking in front of people was one of the hardest things for me. So I practiced my speeches with Steve Jobs videos on YouTube: his tone, the way he builds a sentence, where he stops. It helped a lot. But when I sat down to write my own script, there was no video of Steve saying what I wanted to say.

So I built a model for one writer: me.

## How I trained it

Everything runs on my Mac (M5 Pro, 48 GB).

| Step | Script | What it does |
|---|---|---|
| 1. Collect | `get_audio.sh` | 29 of his talks and interviews, 1980–2011, about 26 hours (yt-dlp). Mostly unscripted, because that's where he *explains* instead of *performs*. |
| 2. Transcribe | `transcribe.sh` | NVIDIA Parakeet v2 (parakeet-mlx). |
| 3. Keep only Steve | `keep_steve.py` | A voiceprint of Steve (SpeechBrain ECAPA) drops interviewers, narrators and the audience. |
| 4. Passages | `make_chunks.py` | 765 clean passages, one idea each, cut at natural pauses. |
| 5. Clean | `clean_steve.py` | A local Qwen3 30B removes stutters and false starts; a check makes sure it only *deleted* words. |
| 6. Pair with my writing | `make_pairs.py` | **The part made for me:** each passage is paired with the same idea written the way I write, so the model learns one job: my writing → how Steve would say it. |
| 7. Train | `train.sh` | Fine-tune Google's open Gemma 4 (12B) with LoRA in mlx-lm. About 40 minutes. |
| 8. Test | `run_eval.py`, `check_eval.py`, `judge.py` | Held-out talks and my own writing, checks for copying, then blind A/B judging (each pair judged twice with A and B swapped). |

`run_v3.sh` and `run_v4.sh` run steps 5–8 in one go.

## Four versions, four lessons

| Version | What changed | What I learned |
|---|---|---|
| v1 | First try | It learned, then started memorizing. I kept the checkpoint from right before that. |
| v2 | A 2.6× bigger base model (Gemma 4 31B) | Not better. The data mattered more than the size. |
| **v3** | Cleaned the stutters out of Steve's side, kept my order of ideas | **Beat v1 8 out of 10 times in a blind test. The one I use.** |
| v4 | + 9 talks of young Steve (1980–1991) | It got wordier, so I kept v3. |

<p><img src="docs/training-v1.png" width="49%" alt="v1 training: practice keeps improving, quiz gets worse after step 200"></p>

**Example.** My writing, first draft, typos and all:
> what if I have this glass that can record me in every converstaion I am in. I have a conversation with this person in te social setting. and when I meet thim next time, I might forget about thier information what was the previous converstion was about. […]

My model (v3):
> What if you have this glass? What if you could record every conversation you are in and never forget what was said to you again? You know, because we meet people in social settings sometimes, and we might not remember everything they told us. […]

## Try the idea yourself

My model is trained on my own writing, so I also made a **copy-paste prompt from the same Steve data**: **[PROMPT.md](PROMPT.md)**. Copy the box into ChatGPT, Gemini or Claude, add your text at the bottom, done. It carries 8 real passages of Steve, so the AI copies how he really talked instead of a movie version of him.

## Command line (macOS)

```bash
git clone https://github.com/minhodongcollege/say-it-like-steve
cd say-it-like-steve
./steve "I made a light bulb mascot because it means ideas."
```

Or copy any text, run `./steve`, and paste: the result is already on your clipboard.

- `./steve --local` runs a model you trained with the steps above (free, offline). That's how I use mine.
- `./steve` without a model of your own sends the PROMPT.md prompt through [Claude Code](https://claude.com/claude-code).

## Train one on your own writing

You need macOS on Apple Silicon, [uv](https://docs.astral.sh/uv/), ffmpeg and yt-dlp. Each script's first lines say how to run it. Two files you make yourself:
- `data/minho_writing.json`: samples of **your** writing for step 6. A list of `{"source": "chat message" | "LinkedIn draft" | "college essay", "text": "..."}`.
- `data/eval/inputs.jsonl`: test texts for step 8. One `{"eid", "source", "input", "steve"}` per line.

## What's not included, and why

- **The full transcripts and training pairs.** Steve's words belong to Apple, Stanford and the other rights holders, so the repo shares the scripts that rebuild them from the public videos, for your own learning.
- **My trained model files,** for the same reason.
- **My personal writing samples and test texts.**

The 8 passages in `PROMPT.md` and `data/eval/baseline_examples.md` are short excerpts from his public talks, shared for learning.

This is a learning project. It is not affiliated with or endorsed by Apple Inc. or the Steve Jobs estate.

## License

Code: MIT (see `LICENSE`). Gemma 4 is released by Google under its own license.

Made by Minho Dong.

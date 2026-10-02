# Vision eye: an external judge that sees what the user sees

**Why.** Gemini's own vision, asked as a judge, keeps passing pictures the user calls horrible. Two examples:
- On 2026-09-23, the source-vs-output judge said "same head angle" on the rocky picture the user called "absolutely horrible".
- A picture-alone coherence question passed 5 of 6 pictures the user called horrible or worst.

The user's words for the defect: "my face alone has been lasso-ed and edited in".

The user asked for free external eyes: a local model, a free API, or a freemium service reachable through an API.

**Rule for any eye.** It must agree with the user on the labelled benchmark before it gates anything in the pipeline:
- flag every "flag" picture;
- pass every "pass" picture.

## Files

| File | What it does |
|---|---|
| `cases.py` | 40 labelled pictures (17 flag, 14 pass, 9 info), each with the user's verdict in their own words |
| `build_bench.py` | Resolves each case's run, source photo and edited region. Saves the views to `.cache\vision_bench\` (not in git; they show the user's face) and writes `manifest.json` |
| `bench.py <eye>` | Runs `eyes\<eye>.py` over the benchmark and prints caught / false alarms, usable or not. Saves `.cache\vision_bench\results_<eye>.json` |
| `eyes\texture.py` | Training-free: face grain and sharpness against its surroundings, compared with the source |
| `eyes\qwen_local.py` | A local vision-language model through llama-server, shown the original and the edited picture side by side |

## Results so far

| Eye | Caught flag pictures | False alarms on pass pictures | Verdict |
|---|---|---|---|
| Gemini, picture alone ("one natural head?") | 1/6 | 0/8 | not usable |
| texture (grain and sharpness vs source) | 10/13 | 11/11 | not usable: every AI face measures sharper against its surroundings, good or bad |
| qwen_local: Qwen3.5-4B Q4_K_M, llama.cpp Vulkan, original and result side by side (2026-09-24) | 5/17 | 4/14 | not usable: chance level (17/31); see below |

Findings for qwen_local:
- **Own photos:** it called nearly every bad picture "clean": rocky F12, both two-heads pictures (F13 and the car2 pair), and F01/F02/F07.
- **It notices, then doesn't flag:** its reason often names the defect ("a slightly different angle or tilt than the rest of the head", "a higher-resolution, sharper version of the original") and still answers `face_pasted: false`.
- **Another man's photo:** it flags any face swap as pasted, good or bad (P05/P06/P11/P14 false alarms), even when told the swap is intended.
- **Speed:** about 100 s per pair.
- **Stability:** the first run died after 19 pictures (4 slots, 8192 context); with 1 slot, 4096 context and auto-restart it finished.
- **Published comparison:** zero-shot face-edit detection with 4-8B vision models is near chance (Forensics-Bench, HydraFake).

| trufor: TruFor (grip-unina), CPU, native-resolution crop plus a real-photo ring, compared with the same crop of the source | 16/17 | 11/14 | not usable as a yes/no gate: every Gemini paste lights up |

**TruFor as a RANKER on his own photos works on this set.**
- **The score:** how much more the face region lights up than the real photo ring around the crop, minus the same number on the untouched source.
- **Result:** within the same source photo, the picture the user disliked scores higher than the one they liked in 16 of 17 pairs:
  - IMG_0862: perfect 0.33 vs two heads 1.04;
  - rocky: liked 0.02-0.58 vs "absolutely horrible" 1.18 and "worse than ever" 0.55 (the one wrong pair: 0.55 vs mt1 0.58);
  - kayak: liked 0.07/0.12 vs 0.19/0.21/0.34;
  - stained glass: 0.41 vs 0.43/0.65.
- **Excluded:** the round-2 rocky output (heuristic blur and relight, a different defect), which it misses.
- **Another man's photo:** useless. The Pinterest head swaps all score 0.89-0.99, and pairs are at chance (21/36).
- **Speed:** about 10 s per crop on this CPU.
- **Caveats:** a small set, and the pairs share pictures, so this is a lead, not proof.
- **Licence:** nonprofit only, so it can be used on the user's own pictures and never in a paid product.

Setup: `D:\VisionModels\TruFor` (git clone, `py -3.11 -m venv venv`, CPU torch 2.14 + `yacs "timm<1" tqdm opencv-python`, the weights zip from grip.unina.it unzipped into `test_docker\weights`). `trufor_test.py` is patched locally with `weights_only=False` (torch>=2.6 default). The eye passes the input folder with a trailing `\`; without it, TruFor writes its results to `C:\`.

## Local model server (llama.cpp, Vulkan on the Intel iGPU)

Installed with `winget install --id ggml.llamacpp -e` (build b11118). The exe is at `%LOCALAPPDATA%\Microsoft\WinGet\Packages\ggml.llamacpp_Microsoft.Winget.Source_8wekyb3d8bbwe\llama-server.exe`. It sees `Vulkan0: Intel(R) UHD Graphics (8013 MiB)`.

The model is stored on D: in `D:\VisionModels\qwen3.5-4b\`: `Qwen3.5-4B-Q4_K_M.gguf` (Apache-2.0) and `mmproj-F16.gguf`.

Start the server in the background, with output redirected so the shell does not hang:

    llama-server.exe -m D:\VisionModels\qwen3.5-4b\Qwen3.5-4B-Q4_K_M.gguf --mmproj D:\VisionModels\qwen3.5-4b\mmproj-F16.gguf
        --port 8093 -ngl 99 -np 1 -c 4096 --temp 0 --image-max-tokens 1024 --reasoning off

Then run the benchmark:

    .venv\Scripts\python.exe research\vision_eye\bench.py qwen_local

Stop the server when done: `Stop-Process -Name llama-server`.

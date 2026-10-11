# CloudKit demo script

This script records a short GIF or Loom video of the CloudKit repository. Target length is about 90 seconds. Every command below runs locally, needs no AWS account, and changes nothing outside the repository. The recording shows what the repository verifies, not a live deployment, because none exists.

## Before you record

1. Use a clean terminal with a large font (at least 16 pt) and a dark or light theme with high contrast.
2. Set the window to about 1200 x 700 pixels. Keep the browser for step 2 at the same size.
3. Install PyYAML once, before recording, so the install does not appear on screen:

   ```bash
   python3 -m pip install "pyyaml==6.0.3"
   ```

4. Change into the repository and clear the screen:

   ```bash
   cd cloudkit
   clear
   ```

5. For a GIF, use a screen recorder that exports GIF (for example Kap or the built-in GIF export of your recorder). For Loom, record the whole screen and keep the microphone off unless you add narration.

## Scene list

| # | Time | What is on screen | Why |
|---|---|---|---|
| 1 | 0:00 to 0:10 | `README.md` rendered, scrolled to the Mermaid diagram | Shows the architecture |
| 2 | 0:10 to 0:20 | `docs/` folder listing, then `docs/ADR-0001-no-nat-gateway.md` | Shows that decisions are recorded |
| 3 | 0:20 to 0:40 | Terminal: unit tests | Shows the checks that run without credentials |
| 4 | 0:40 to 0:55 | Terminal: teardown dry run | Shows that teardown does nothing by default |
| 5 | 0:55 to 1:15 | Terminal: `scripts/validate.sh` | Shows that missing tools are reported as SKIP, not as passing |
| 6 | 1:15 to 1:30 | `.github/workflows/ci.yml` in the editor | Shows the CI jobs |

## Steps

### Scene 1: Architecture

1. Open `README.md` in a Markdown preview.
2. Scroll until the Mermaid diagram is in the middle of the frame.
3. Pause for 3 seconds so the diagram is readable.
4. Say (for narration): "CloudFront fronts an ALB and an ECS Fargate task. RDS sits in private subnets."

### Scene 2: Decisions

1. In the file tree, open the `docs/` folder.
2. Click `ADR-0001-no-nat-gateway.md`.
3. Scroll to the Decision section and pause for 3 seconds.
4. Say: "Each key decision has an ADR with its consequences."

### Scene 3: Unit tests

1. Switch to the terminal.
2. Type this command and press Enter:

   ```bash
   python3 -m unittest discover -s tests -v
   ```

3. Wait for the summary line that begins with `Ran`. Hold it on screen for 3 seconds.
4. Expected output on the last lines: `Ran 119 tests` and `OK` (the count on the local machine). If your count differs, record what you see and do not edit this script.

### Scene 4: Teardown dry run

1. Type:

   ```bash
   bash scripts/teardown.sh --dry-run
   ```

2. Point out the lines that begin with `DRY-RUN:`. Say: "Teardown never runs by default. It prints the steps and stops."
3. Hold for 3 seconds.

### Scene 5: Validation with missing tools

1. Type:

   ```bash
   bash scripts/validate.sh
   ```

2. When the `SKIP:` lines appear, say: "Terraform, Ansible and shellcheck are not installed on this machine, so their checks are skipped. A skip is not a pass."
3. Hold on the `validate exit code` line for 3 seconds.
4. If Terraform is installed on your machine, the Terraform lines run instead of skipping. Record what you see, and do not claim results you did not see.

Note: this run writes a new timestamped file into `docs/proof/`. Delete that new file after recording if you do not want to keep it.

### Scene 6: CI

1. Open `.github/workflows/ci.yml`.
2. Scroll through the four job names: `static-tests`, `shellcheck`, `terraform-offline`, `ansible-syntax`.
3. End on the `on:` block so the viewer sees the triggers.

## After recording

1. Trim the start and end so the video is under 90 seconds.
2. Export the GIF at 800 pixels wide or less to keep the file small.
3. Save the GIF under `docs/` (for example `docs/demo.gif`) and add it to the README only after you have recorded it. Do not add a placeholder image that has no real content.
4. Replace the Loom link in your notes with the real link after you upload it.

## What not to show

- Do not show a real AWS account, console or access key.
- Do not show `.env`, `backend.hcl` or `terraform.tfvars` if you created them locally.
- Do not run any command that talks to AWS or GitHub during the recording.

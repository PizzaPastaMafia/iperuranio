# Auto-deploy master

The server checks GitHub every minute. When `master` has a new commit it pulls it, and nginx serves the new files straight away, because `web/html` is bind-mounted from the checkout. Nothing runs in GitHub and the server needs no open ports or webhooks.

The pieces:

- `auto-update.sh`: fetches `origin/master` and, if it moved, resets the checkout to it, fixes the file permissions, and runs `docker compose up -d` only if `web/docker-compose.yml` changed. When nothing changed it exits silently.
- `iperuranio-update.service` and `iperuranio-update.timer`: a systemd timer that runs the script every minute.

## One-time setup on the server

These steps assume the checkout lives in `/opt/iperuranio` and belongs to a user called `deploy`. Use your own path and user, and change them in `iperuranio-update.service` to match.

1. **Clone the repo** to its permanent home. The repo is public, so no key is needed:

   ```sh
   sudo mkdir -p /opt/iperuranio && sudo chown deploy: /opt/iperuranio
   sudo -u deploy git clone -b master https://github.com/PizzaPastaMafia/iperuranio.git /opt/iperuranio
   ```

   If the repo ever becomes private, give the server read-only access with a deploy key: run `sudo -u deploy ssh-keygen -t ed25519 -N "" -f ~deploy/.ssh/iperuranio`, add the `.pub` file under the repo's **Settings → Deploy keys** (leave "Allow write access" off), then inside the checkout run `git remote set-url origin git@github.com:PizzaPastaMafia/iperuranio.git` and `git config core.sshCommand "ssh -i ~/.ssh/iperuranio"`.

2. **Move the site onto the clone.** If the site is currently running from copied files (not a git clone), switch it over once. It is down for a few seconds while the container restarts; Traefik picks it up again from the same labels.

   ```sh
   cp /path/to/old/web/.env /opt/iperuranio/web/.env
   (cd /path/to/old/web && docker compose down)
   (cd /opt/iperuranio/web && docker compose up -d)
   ```

   Check that the site loads, then delete or archive the old folder. Compose names the container after the folder (here `web-website-1`), so it only changes if the old folder had a different name; that matters only if something else refers to the container by name.

   On a brand-new server, just copy `web/.env.example` to `web/.env`, fill it in, and run `docker compose up -d` in `/opt/iperuranio/web`.

3. **Let the `deploy` user run Docker**, so the script can recreate the container when the compose file changes: `sudo usermod -aG docker deploy`. If you'd rather not, set `User=root` in the service file instead.

4. **Install and start the timer**:

   ```sh
   sudo cp /opt/iperuranio/deploy/iperuranio-update.{service,timer} /etc/systemd/system/
   sudoedit /etc/systemd/system/iperuranio-update.service   # check User= and the path
   sudo systemctl daemon-reload
   sudo systemctl enable --now iperuranio-update.timer
   ```

## Checking that it works

```sh
systemctl list-timers iperuranio-update.timer   # when it last ran and runs next
journalctl -u iperuranio-update.service -n 20   # "Updating … -> …" and "Live at …" lines
sudo systemctl start iperuranio-update.service  # run it once right now
```

## Notes

- The script makes the checkout match `master` exactly, so don't edit tracked files on the server; they will be overwritten on the next update. Untracked files such as `web/.env` are kept.
- To deploy another branch, add `Environment=BRANCH=other-branch` to the service file.

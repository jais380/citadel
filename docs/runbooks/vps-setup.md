# Runbook: VPS setup and hardening

The VPS runs Caddy, n8n and the portfolio. It must be **Citadel's own server**, never an
employer's. Run these steps on the server itself, over SSH, not through a remote Docker context
from the laptop (bind mounts like the Caddyfile would point at laptop paths).

## 1. Harden before installing anything

```bash
# as root, once
adduser citadel
usermod -aG sudo citadel
mkdir -p /home/citadel/.ssh && cp ~/.ssh/authorized_keys /home/citadel/.ssh/
chown -R citadel:citadel /home/citadel/.ssh && chmod 700 /home/citadel/.ssh

# confirm you can log in as citadel with your key in a NEW terminal, then:
sudo sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/; s/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

sudo ufw default deny incoming && sudo ufw default allow outgoing
sudo ufw allow 22/tcp && sudo ufw allow 80/tcp && sudo ufw allow 443/tcp && sudo ufw allow 443/udp
sudo ufw enable

sudo apt update && sudo apt install -y unattended-upgrades fail2ban
```

Never close the root session until the `citadel` login works, or you can lock yourself out.

Docker publishes ports by writing its own firewall rules, which bypass ufw. Only Caddy
publishes ports in `infra/vps/docker-compose.yml`; keep it that way.

## 2. Install Docker and Tailscale

Follow Docker's official Ubuntu instructions, then `sudo usermod -aG docker citadel` and log in
again. Install Tailscale and run `sudo tailscale up` on the same tailnet as the laptop.

## 3. Deploy the stack

```bash
git clone <your citadel repo> && cd citadel/infra/vps
cp .env.example .env && nano .env      # DOMAIN, ACME_EMAIL, secrets, CITADEL_URL
docker compose up -d
docker compose logs -f caddy           # watch certificates being issued
```

DNS A records for `@`, `n8n` and `tools` must point at the server before starting.

## 4. Secure n8n

- Create the owner account immediately after first start (the first visitor becomes owner).
- **Back up `N8N_ENCRYPTION_KEY`** in a password manager. Losing it loses every stored credential.
- Create the API key under Settings → n8n API; store it in a password manager.
- Workflows that send messages or change data stay inactive until reviewed (G9).

## 5. Check the link to the laptop

```bash
curl http://<laptop-tailscale-ip>:8000/health   # expect: ok
```

## Backups

| What | How | How often |
|---|---|---|
| n8n database | `docker compose exec n8n-db pg_dump -U n8n n8n > n8n-$(date +%F).sql` | Daily (cron) |
| n8n workflows | Export to JSON and commit to a private repo | After every change |
| Encryption key and `.env` | Password manager | Once, and on change |

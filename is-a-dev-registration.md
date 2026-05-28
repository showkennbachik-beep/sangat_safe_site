# How to Get Your Free Domain: sangat-tools.is-a.dev

is-a.dev gives free subdomains to developers. Follow these steps:

## Steps (takes 5 minutes, approved in 1–2 days)

### 1. Go to the registration repo
https://github.com/is-a-dev/register

### 2. Fork the repo
Click the **Fork** button (top right) → Fork to your account.

### 3. Create a new file
In your forked repo, go to the `domains/` folder.
Click **Add file → Create new file**.
Name it: `sangat-tools.json`

### 4. Paste this content (replace TUNNEL_UUID with your real UUID from setup)

```json
{
  "description": "SANGAT Tools — Free PDF and Image toolkit",
  "repo": "https://github.com/showkennbachik-beep/sangat_safe_site",
  "owner": {
    "username": "showkennbachik-beep",
    "email": "duroog3@gmail.com"
  },
  "record": {
    "CNAME": "TUNNEL_UUID.cfargotunnel.com"
  }
}
```

> Your TUNNEL_UUID is shown after running cloudflare-setup.ps1

### 5. Submit a Pull Request
- Click **Commit changes** (commit directly to your fork)
- Click **Contribute → Open Pull Request**
- Title: `add sangat-tools`
- Submit it

### 6. Wait for approval
The is-a.dev maintainers review and merge PRs within **1–2 days**.
Once merged, `https://sangat-tools.is-a.dev` will point to your tunnel.

### 7. Go live permanently
```powershell
.\cloudflare-start.ps1
```

Your site is now live at **https://sangat-tools.is-a.dev** — forever, for free.

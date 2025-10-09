# Claude Code Vision - Quick Start Demo

## 🎯 Použitie Claude Code Vision

### Príprava
```bash
cd /home/patrik/spec-kit-demo/demo-project
source venv/bin/activate
```

### 1. Základné Príkazy (Fungujú Okamžite)

#### Diagnostika Systému
```bash
claude-vision doctor
```
**Čo robí:** Skontroluje všetky závislosti, screenshot tools, Python verziu, atď.

#### Test Screenshot Capture
```bash
claude-vision test-capture
```
**Čo robí:** Zachytí screenshot a overí že všetko funguje

#### Zoznam Monitorov
```bash
claude-vision list-monitors
```
**Čo robí:** Zobrazí všetky pripojené monitory

#### Validácia Konfigurácie
```bash
claude-vision validate-config
```
**Čo robí:** Skontroluje config.yaml a upozorní na problémy

---

### 2. Vision Commands (Vyžadujú Claude Code OAuth)

**POZNÁMKA:** Tieto príkazy potrebujú Claude Code OAuth token na komunikáciu s Claude API.

#### /vision - Celý Screen
```bash
claude-vision vision "What do you see on my screen?"
```
**Čo robí:**
1. Zachytí celú obrazovku
2. Optimizuje screenshot (max 2 MB)
3. Aplikuje privacy zones (ak sú nastavené)
4. Pošle Claude API s tvojím promptom
5. Vráti odpoveď od Claude

#### /vision.area - Výber Oblasti
```bash
# S grafickým výberom (potrebuje slop/slurp)
claude-vision area "Analyze this region"

# Alebo s koordinátmi (funguje vždy)
claude-vision area --coords "100,100,800,600" "What's in this area?"
```
**Čo robí:** Zachytí len vybranú oblasť obrazovky

#### /vision.auto - Auto-monitoring
```bash
# Spustí auto-monitoring (každých 30 sekúnd)
claude-vision auto

# Zastav monitoring
claude-vision stop
```
**Čo robí:** Periodicky zachytáva screenshots a sleduje zmeny

---

### 3. Privacy Zones (Ochrana Citlivých Oblastí)

#### Pridaj Privacy Zone
```bash
claude-vision add-privacy-zone
```
Interaktívne pridá oblasť na začiernenie (napr. pre password managery)

#### Zoznam Privacy Zones
```bash
claude-vision list-privacy-zones
```

#### Odstráň Privacy Zone
```bash
claude-vision remove-privacy-zone
```

---

## 🔧 Integrácia s Claude Code

### Vytvorenie Slash Commands v Claude Code

**1. Vytvor Custom Slash Commands:**

```bash
mkdir -p ~/.claude/commands/
```

**2. Vytvor `/vision` command:**

```bash
cat > ~/.claude/commands/vision.md << 'EOF'
# Vision Command

Execute vision analysis with screenshot capture.

## Usage
/vision [prompt]

## Implementation
Execute: claude-vision vision "$ARGUMENTS"
EOF
```

**3. Vytvor `/vision.area` command:**

```bash
cat > ~/.claude/commands/vision_area.md << 'EOF'
# Vision Area Command

Analyze specific screen region.

## Usage
/vision.area [--coords x,y,w,h] [prompt]

## Implementation
Execute: claude-vision area $ARGUMENTS
EOF
```

**4. Vytvor `/vision.auto` command:**

```bash
cat > ~/.claude/commands/vision_auto.md << 'EOF'
# Vision Auto-monitoring

Start auto-monitoring session.

## Usage
/vision.auto

## Implementation
Execute: claude-vision auto
EOF
```

**5. Reštartuj Claude Code** aby načítal nové commands.

---

## ⚡ Rýchle Demo Scenáre

### Scenár 1: Analýza Kódu na Obrazovke
```bash
# Otvor súbor v editore
code src/cli/main.py

# Zachyť a analyzuj
claude-vision test-capture --open

# Alebo priamo s Claude (vyžaduje OAuth)
claude-vision vision "Review this Python code for potential bugs"
```

### Scenár 2: UI/UX Feedback
```bash
# Otvor webstránku alebo aplikáciu
firefox https://example.com

# Analyzuj dizajn
claude-vision vision "What are the main UX issues with this interface?"
```

### Scenár 3: Debugging Vizuálneho Bugu
```bash
# Zachyť bug
claude-vision area --coords "500,300,400,400" "Why is this button not aligned?"
```

### Scenár 4: Privacy-Safe Screenshot
```bash
# Najprv nastav privacy zones
claude-vision add-privacy-zone
# (Vyber oblasť kde je password manager)

# Potom zachyť screen - citlivé oblasti budú začiernené
claude-vision vision "Help me with this configuration"
```

---

## 🚨 Troubleshooting

### Problém: "No screenshot tool found"

**Riešenie:**
```bash
# X11
sudo apt install scrot -y

# Wayland
sudo apt install grim -y

# Fallback (funguje vždy)
sudo apt install imagemagick -y

# Overenie
claude-vision doctor
```

### Problém: "No display available"

**Riešenie:**
```bash
# Skontroluj DISPLAY
echo $DISPLAY

# Ak je prázdne, nastav
export DISPLAY=:0

# Pre Wayland
echo $WAYLAND_DISPLAY
```

### Problém: "OAuth token not found"

**Toto je OČAKÁVANÉ** - vyžaduje integráciu s Claude Code OAuth.

**Dočasné riešenie pre testing:**
```bash
# Vytvor mock OAuth config (len pre development)
mkdir -p ~/.claude
cat > ~/.claude/config.json << 'EOF'
{
  "token": "sk-ant-test-token-placeholder"
}
EOF
```

**Produkčné riešenie:**
- Použiť Claude Code cez oficiálny CLI
- Token sa automaticky zdieľa

### Problém: "Region selector not found"

**Riešenie:**
```bash
# Pre Wayland
sudo apt install slurp -y

# Pre X11
sudo apt install slop -y

# Alebo použi --coords parameter
claude-vision area --coords "0,0,800,600" "analyze this"
```

### Problém: Screenshot je príliš veľký

**Riešenie:**
```bash
# Uprav config
nano ~/.config/claude-code-vision/config.yaml

# Zmeň:
screenshot:
  quality: 75  # Zníž z 85 na 75
  max_size_mb: 1.5  # Zníž z 2.0 na 1.5
```

---

## 📋 Užitočné Príkazy

### Celý Workflow
```bash
# 1. Diagnostika
claude-vision doctor

# 2. Test
claude-vision test-capture

# 3. Validácia
claude-vision validate-config

# 4. Použitie (priamo alebo cez Claude Code)
claude-vision vision "Your prompt here"
```

### Monitoring Session
```bash
# Spusti monitoring
claude-vision auto --interval 60

# V inom terminále sleduj logy
tail -f ~/.config/claude-code-vision/vision.log

# Zastav
claude-vision stop
```

### Cleanup
```bash
# Vyčisti temp files
rm -rf /tmp/claude-vision/*

# Reset config
claude-vision init --force
```

---

## 🎓 Best Practices

### 1. Privacy First
- Vždy nastav privacy zones pred použitím na práci
- Skontroluj config pred každým použitím
- Nepoužívaj v citlivých situáciách bez privacy zones

### 2. Performance
- Použi `--coords` namiesto grafického výberu pre skripty
- Zníž kvalitu pre rýchlejšie spracovanie
- Použi `/vision.area` namiesto `/vision` pre malé detaily

### 3. Debugging
- Vždy začni s `--doctor`
- Použi `--test-capture` pred použitím vision commands
- Sleduj logy: `tail -f ~/.config/claude-code-vision/vision.log`

---

## 📚 Ďalšie Kroky

1. **Prečítaj:** `README.md` pre detailnú dokumentáciu
2. **Prečítaj:** `CONTRIBUTING.md` pre development guide
3. **Pozri:** `specs/002-claude-code-vision/` pre technické detaily
4. **Testuj:** `pytest tests/` pre spustenie testov

---

## 💡 Tip: Alias pre Rýchle Použitie

Pridaj do `~/.bashrc` alebo `~/.zshrc`:

```bash
alias vision='source ~/spec-kit-demo/demo-project/venv/bin/activate && claude-vision vision'
alias vision-area='source ~/spec-kit-demo/demo-project/venv/bin/activate && claude-vision area'
alias vision-test='source ~/spec-kit-demo/demo-project/venv/bin/activate && claude-vision test-capture'
```

Potom použi jednoducho:
```bash
vision "What do you see?"
vision-area --coords "100,100,500,500" "Analyze this"
vision-test
```

---

**Happy Vision Testing! 🎉**

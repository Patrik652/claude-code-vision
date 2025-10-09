# 🚀 Gemini API Integration - Setup Guide

## ✅ Čo je hotové

Claude Code Vision teraz podporuje **Google Gemini 2.5 Pro API** ako alternatívu k Claude API!

### Nové funkcie:
- ✅ Gemini API klient s vision podporou
- ✅ Automatický výber providera (Claude/Gemini)
- ✅ Fallback systém (ak jeden provider zlyhá, skúsi druhý)
- ✅ Plná podpora multimodálnych promptov
- ✅ Konfigurovateľný model selection

## 📋 Rýchly setup

### 1. Získaj Gemini API kľúč

1. Choď na: https://aistudio.google.com/apikey
2. Vytvor nový API kľúč
3. Skopíruj kľúč

### 2. Konfiguruj API kľúč

**Možnosť A: Config súbor (odporúčané)**

Uprav `~/.config/claude-code-vision/config.yaml`:

```yaml
ai_provider:
  provider: gemini  # Použiť Gemini ako primárny provider
  fallback_to_gemini: true  # Ak Claude zlyhá, skúsi Gemini

gemini:
  api_key: 'AIza...'  # Tvoj Gemini API kľúč
  model: gemini-2.0-flash-exp  # Model na použitie
```

**Možnosť B: Environment variable**

```bash
export GEMINI_API_KEY="AIza..."
```

### 3. Otestuj inštaláciu

```bash
source venv/bin/activate
claude-vision vision "What do you see on my screen?"
```

## 🎯 Dostupné modely

Môžeš vybrať z týchto Gemini modelov v `config.yaml`:

- `gemini-2.0-flash-exp` (odporúčané - najrýchlejší)
- `gemini-1.5-pro` (výkonný, vyvážený)
- `gemini-1.5-flash` (rýchly, úsporný)

## ⚙️ Konfiguračné možnosti

### Použiť len Gemini

```yaml
ai_provider:
  provider: gemini
  fallback_to_gemini: false
```

### Použiť Claude s Gemini fallback

```yaml
ai_provider:
  provider: claude
  fallback_to_gemini: true  # Ak Claude zlyhá, skúsi Gemini
```

### Použiť Gemini s Claude fallback

```yaml
ai_provider:
  provider: gemini
  fallback_to_gemini: true  # Ak Gemini zlyhá, skúsi Claude
```

## 🔍 Debugging

Ak niečo nefunguje, skontroluj logy:

```bash
tail -f ~/.config/claude-code-vision/vision.log
```

Hľadaj riadky:
- `Using Gemini API as primary provider` ✅
- `Gemini API client initialized` ✅
- `Gemini API client not available: ...` ❌

## 💡 Výhody Gemini API

1. **Rýchlejšie odpovede** - Gemini 2.0 Flash je extrémne rýchly
2. **Väčšie limity** - Až 20MB obrázky (vs 5MB pre Claude)
3. **Lacnejšie** - Gemini API má nižšie ceny
4. **Flexibilita** - Viac modelov na výber

## 🆚 Claude vs Gemini

| Feature | Claude | Gemini |
|---------|--------|--------|
| Max image size | 5 MB | 20 MB |
| Response speed | Fast | Very Fast |
| Vision quality | Excellent | Excellent |
| API cost | Higher | Lower |
| Models | Sonnet, Opus | Flash, Pro |

## 🐛 Časté problémy

### "Gemini API client not available"

**Riešenie:**
1. Skontroluj, či je API kľúč správny
2. Skontroluj, či je `google-generativeai` nainštalovaný:
   ```bash
   pip list | grep google-generativeai
   ```

### "API quota exceeded"

**Riešenie:**
- Skontroluj limity na https://aistudio.google.com/
- Počkaj pár minút a skús znova
- Prepni na Claude provider dočasne

### "Model not found"

**Riešenie:**
- Skontroluj dostupné modely na https://ai.google.dev/models/gemini
- Uprav `config.yaml` s platným model menom

## 📚 Príklady použitia

### Základné príkazy

```bash
# Jednoduchý vision príkaz
claude-vision vision "Describe what you see"

# S konkrétnou otázkou
claude-vision vision "What programming language is shown in this code?"

# Multi-monitor support
claude-vision vision --monitor 1 "What's on my second screen?"

# Area selection (grafický výber)
claude-vision area "What is this UI component?"

# Area selection (pomocou koordinátov)
claude-vision area --coords "100,100,800,600" "Analyze this region"
```

### Utility príkazy

```bash
# Diagnostika systému
claude-vision --doctor

# Zoznam monitorov
claude-vision --list-monitors

# Validácia konfigurácie
claude-vision --validate-config

# Test screenshot capture
claude-vision --test-capture
```

## 🎓 Ďalšie zdroje

- Gemini API docs: https://ai.google.dev/docs
- Modely: https://ai.google.dev/models/gemini
- Pricing: https://ai.google.dev/pricing
- API kľúče: https://aistudio.google.com/apikey

## ✅ Status

Systém je **plne funkčný** a pripravený na použitie! Gemini API poskytuje skvelú alternatívu k Claude API s rýchlymi odpoveďami a väčšími limitmi.

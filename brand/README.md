# KS1 PRODUÇÕES — Identidade Visual

Marca **vetorizada a partir do logo original** (`foto logo ks1.png`) — pincelada/brush
fiel, com os furos das letras preservados via `fill-rule="evenodd"`. 100% SVG,
escalável sem perda, sem imagens raster. Inclui também a assinatura do **DJ Kennim**.

Abra `preview.html` no navegador para ver tudo.

## Logos (SVG vetorial)

| Arquivo | Uso |
|---|---|
| `ks1-logo-principal.svg` | Logo principal — branco sobre fundo preto |
| `ks1-logo-pb.svg` | Preto & branco puro (1 cor, impressão) |
| `ks1-logo-fundo-claro.svg` | Marca preta sobre fundo claro |
| `ks1-logo-transparente.svg` | Marca **branca**, fundo transparente (usar em fundo escuro/foto) |
| `ks1-logo-transparente-preto.svg` | Marca **preta**, fundo transparente (usar em fundo claro) |
| `ks1-logo-horizontal.svg` | Lockup horizontal — KS1 + PRODUÇÕES + tagline |
| `ks1-logo-contato.svg` | Assinatura de marca com e-mail e WhatsApp |
| `ks1-icon.svg` | Ícone/avatar quadrado — foto de perfil de redes sociais |
| `kennim-assinatura.svg` | Assinatura DJ Kennim sobre preto |
| `kennim-assinatura-transparente.svg` | Assinatura DJ Kennim, fundo transparente |

## PNG (alta resolução, pasta `png/`)

Versões rasterizadas prontas pra postar (Instagram, WhatsApp, flyers). Os
`*-transparente*.png` têm fundo transparente real. Pra gerar de novo / em outro
tamanho, veja "Reproduzir" abaixo.

## Paleta oficial

- Preto profundo `#0A0A0C` (fundo padrão)
- Branco gelo `#F5F6F8` (marca)
- Azul elétrico `#1E50FF` + Azul neon `#38BDF8` (acento musical premium — disponível pra usar em peças)

## Contato oficial

- 📧 Djkennim@gmail.com
- 📞 / WhatsApp: +55 31 9795-2897

## Reproduzir / regenerar

Os SVGs são gerados a partir dos PNGs originais (em `ref/`) por vetorização:

```bash
pip install opencv-python-headless numpy pillow
python build.py          # regera todos os SVGs
```

Exportar PNGs (usa Chrome headless):

```powershell
# ver o bloco de export no histórico — render via:
chrome --headless --screenshot=out.png --window-size=W,H arquivo.svg
```

- `trace.py` — vetoriza um PNG (contornos → curvas Bézier suaves).
- `build.py` — separa KS1 / PRODUÇÕES por área e monta todas as variações.
- `ref/` — PNGs originais de referência.

> Para gráfica/impressão profissional, os textos auxiliares (PRODUÇÕES da versão
> horizontal usa o brush vetorizado; a tagline e os contatos usam fonte Arial) —
> converta as fontes em curvas no fechamento da arte final.

# Bibliotecas de terceiros (servidas localmente)

| Pasta | Versão | Origem | Arquivos |
|---|---|---|---|
| `bootstrap-5.3.3/` | Bootstrap 5.3.3 (MIT) | `npm: bootstrap@5.3.3/dist` | `bootstrap.min.css`, `bootstrap.bundle.min.js` e os `.map` |
| `phosphor-2.1.1/` | Phosphor Icons 2.1.1 (MIT) | `npm: @phosphor-icons/web@2.1.1/src` | `regular/` e `fill/`: `style.css` + fonte `.woff2` |

- Bootstrap conferido pelos hashes SRI oficiais da 5.3.3:
  - `bootstrap.min.css`: `sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH`
  - `bootstrap.bundle.min.js`: `sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz`
- Phosphor: o `@font-face` de cada `style.css` foi reduzido para apontar só para o `.woff2`
  (os formatos woff, ttf e svg não são distribuídos). Nenhuma outra alteração.
- Os `.map` do Bootstrap ficam junto porque o `collectstatic` de produção
  (`CompressedManifestStaticFilesStorage`) resolve as referências `sourceMappingURL`.

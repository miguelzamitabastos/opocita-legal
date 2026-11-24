#!/usr/bin/env python3
"""Genera la web legal de OpoCita desde docs/legal/*.md (sólo librería estándar).

Uso: python3 build.py [carpeta_de_origen]
Por defecto lee ~/proyects/OpoCita/docs/legal/ y escribe junto a este script.
"""
import html
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ORIGEN = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/proyects/OpoCita/docs/legal')

# Datos del titular: viven sólo aquí (la web legal), nunca en el repo de la app.
DATOS = {
    '{{NOMBRE}}': 'Miguel Zamit Monsalve',
    '{{NIF}}': '23822057Z',
    '{{DOMICILIO}}': 'Calle Rodrigo Canto 31, 1º, 46133 Meliana (Valencia)',
    '{{CORREO}}': 'soporteopocita@gmail.com',
    '{{FECHA}}': '24 de noviembre de 2026',
}

PAGINAS = [  # (fichero md, carpeta de salida)
    ('soporte.md', ''),
    ('privacidad.md', 'privacidad'),
    ('aviso-legal.md', 'aviso-legal'),
    ('terminos.md', 'terminos'),
]

CSS = """
:root{color-scheme:light dark;--fondo:#fff;--texto:#1c1c1e;--suave:#5f6368;--enlace:#0b57d0;--linea:#d8dadd;--cab:#f3f4f6}
@media (prefers-color-scheme:dark){:root{--fondo:#121212;--texto:#e8eaed;--suave:#a0a4a8;--enlace:#8ab4f8;--linea:#3c4043;--cab:#202124}}
*{box-sizing:border-box}
body{margin:0;background:var(--fondo);color:var(--texto);font:17px/1.6 -apple-system,system-ui,"Segoe UI",Roboto,sans-serif}
main{max-width:46rem;margin:0 auto;padding:1.25rem 1rem 3rem}
h1{font-size:1.7rem;line-height:1.25;margin:1rem 0}
h2{font-size:1.3rem;margin:2rem 0 .5rem}
h3{font-size:1.1rem;margin:1.5rem 0 .4rem}
a{color:var(--enlace)}
ul,ol{padding-left:1.4rem}
li{margin:.25rem 0}
code{font:.9em ui-monospace,Menlo,monospace;background:var(--cab);padding:.1em .3em;border-radius:4px}
pre{background:var(--cab);padding:.75rem;border-radius:6px;overflow-x:auto}
pre code{background:none;padding:0}
.tabla{overflow-x:auto}
table{border-collapse:collapse;width:100%;margin:1rem 0}
th,td{border:1px solid var(--linea);padding:.4rem .6rem;text-align:left;vertical-align:top}
th{background:var(--cab)}
nav{font-size:.95rem;color:var(--suave);border-bottom:1px solid var(--linea);padding-bottom:.6rem}
nav a{margin-right:.9rem}
"""

NAV = [('Soporte', ''), ('Privacidad', 'privacidad'), ('Aviso legal', 'aviso-legal'), ('Condiciones', 'terminos')]


def en_linea(t):
    """Markdown en línea: código, enlaces, negrita y cursiva (con el HTML escapado)."""
    trozos = []

    def guardar(h):
        trozos.append(h)
        return '\x00%d\x00' % (len(trozos) - 1)

    t = re.sub(r'`([^`]+)`', lambda m: guardar('<code>%s</code>' % html.escape(m.group(1))), t)
    t = re.sub(
        r'\[([^\]]+)\]\(([^)\s]+)\)',
        lambda m: guardar('<a href="%s">%s</a>' % (html.escape(m.group(2), quote=True), en_linea(m.group(1)))),
        t,
    )
    t = html.escape(t, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', t)
    t = re.sub(r'(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])', r'<em>\1</em>', t)
    t = re.sub(r'(?<!["\w/])(https?://[^\s<)]+[^\s<).,;])', r'<a href="\1">\1</a>', t)
    return re.sub(r'\x00(\d+)\x00', lambda m: trozos[int(m.group(1))], t)


def celdas(linea):
    return [c.strip() for c in linea.strip().strip('|').split('|')]


def md_a_html(md):
    lineas = md.split('\n')
    out, i, titulo = [], 0, ''
    while i < len(lineas):
        l = lineas[i]
        if not l.strip():
            i += 1
        elif l.startswith('```'):
            i += 1
            cod = []
            while i < len(lineas) and not lineas[i].startswith('```'):
                cod.append(lineas[i])
                i += 1
            i += 1
            out.append('<pre><code>%s</code></pre>' % html.escape('\n'.join(cod)))
        elif re.match(r'#{1,6} ', l):
            n = len(l) - len(l.lstrip('#'))
            txt = l[n:].strip()
            if n == 1 and not titulo:
                titulo = txt
            out.append('<h%d>%s</h%d>' % (n, en_linea(txt), n))
            i += 1
        elif l.lstrip().startswith('|') and i + 1 < len(lineas) and re.match(r'^\s*\|[\s:|-]+\|\s*$', lineas[i + 1]):
            cab = celdas(l)
            i += 2
            filas = []
            while i < len(lineas) and lineas[i].lstrip().startswith('|'):
                filas.append(celdas(lineas[i]))
                i += 1
            h = '<div class="tabla"><table><thead><tr>%s</tr></thead><tbody>' % ''.join(
                '<th>%s</th>' % en_linea(c) for c in cab)
            for f in filas:
                h += '<tr>%s</tr>' % ''.join('<td>%s</td>' % en_linea(c) for c in f)
            out.append(h + '</tbody></table></div>')
        elif re.match(r'\s*([-*]|\d+\.) ', l):
            orden = bool(re.match(r'\s*\d+\. ', l))
            items = []
            while i < len(lineas) and lineas[i].strip():
                m = re.match(r'\s*(?:[-*]|\d+\.) (.*)', lineas[i])
                if m:
                    items.append(m.group(1))
                elif re.match(r'\s+\S', lineas[i]) and items:
                    items[-1] += ' ' + lineas[i].strip()
                else:
                    break
                i += 1
            etq = 'ol' if orden else 'ul'
            out.append('<%s>%s</%s>' % (etq, ''.join('<li>%s</li>' % en_linea(x) for x in items), etq))
        else:
            par = []
            while i < len(lineas) and lineas[i].strip() and not re.match(r'#{1,6} |```|\s*([-*]|\d+\.) ', lineas[i]):
                par.append(lineas[i].strip())
                i += 1
            out.append('<p>%s</p>' % en_linea(' '.join(par)))
    return '\n'.join(out), titulo


def pagina(cuerpo, titulo, carpeta):
    prof = '' if not carpeta else '../'
    nav = ''.join('<a href="%s">%s</a>' % ((prof + d + '/') if d else (prof or './'), n) for n, d in NAV)
    return ('<!DOCTYPE html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n<main>\n<nav>%s</nav>\n%s\n</main>\n</body>\n</html>\n'
            % (html.escape(titulo), CSS, nav, cuerpo))


def main():
    for fichero, carpeta in PAGINAS:
        with open(os.path.join(ORIGEN, fichero), encoding='utf-8') as f:
            md = f.read()
        for k, v in DATOS.items():
            md = md.replace(k, v)
        cuerpo, titulo = md_a_html(md)
        destino = os.path.join(AQUI, carpeta)
        os.makedirs(destino, exist_ok=True)
        with open(os.path.join(destino, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(pagina(cuerpo, titulo or 'OpoCita', carpeta))
        print('escrito', os.path.join(carpeta, 'index.html'))


if __name__ == '__main__':
    main()

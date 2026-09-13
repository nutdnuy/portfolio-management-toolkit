"""Export the project's editable Excalidraw teaching scenes to self-contained SVG.

Uses only the standard library. Supported scene primitives are deliberately
small: unrotated rectangles, ellipses, text, lines and single-ended arrows.
The JSON scene is the source of all positions, values and geometry.
"""
import base64
import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def esc(value):
    return html.escape(str(value), quote=True)

def font_css():
    rules = []
    for family, filename in [('DiagramRoboto','roboto-latin-400-normal.woff2'),
                             ('DiagramThai','noto-sans-thai-thai-400-normal.woff2')]:
        data = base64.b64encode((ROOT/'assets/fonts'/filename).read_bytes()).decode()
        rules.append(f'@font-face{{font-family:{family};src:url(data:font/woff2;base64,{data}) format("woff2");font-weight:400;}}')
    return ''.join(rules)

def export(scene):
    meta = scene['toolkit']
    w,h=meta['width'],meta['height']
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',
           f'<title id="title">{esc(meta["title"])}</title><desc id="desc">{esc(meta["description"])}</desc>',
           f'<style>{font_css()}text{{font-family:DiagramRoboto,DiagramThai,Arial,sans-serif;font-weight:400;}}</style>']
    for e in scene['elements']:
        if e.get('isDeleted'): continue
        if e.get('angle',0): raise ValueError('Rotated elements are not supported')
        x,y,w,h=e['x'],e['y'],e['width'],e['height']
        color,fill=esc(e['strokeColor']),esc(e['backgroundColor'])
        if fill=='transparent': fill='none'
        sw=e.get('strokeWidth',2)
        dash=' stroke-dasharray="9 7"' if e.get('strokeStyle')=='dashed' else ''
        base=f'id="{esc(e["id"])}" stroke="{color}" stroke-width="{sw}" fill="{fill}"{dash}'
        kind=e['type']
        if kind=='rectangle': parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" {base}/>')
        elif kind=='ellipse': parts.append(f'<ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" {base}/>')
        elif kind=='text':
            alignment=e.get('textAlign','left')
            anchor={'left':'start','center':'middle','right':'end'}[alignment]
            tx=x+({'left':0,'center':w/2,'right':w}[alignment])
            size=e['fontSize']
            for n,label in enumerate(e['text'].split('\n')):
                ty=y+size*1.05+n*size*e['lineHeight']
                parts.append(f'<text id="{esc(e["id"])}-{n}" x="{tx}" y="{ty}" font-size="{size}" text-anchor="{anchor}" fill="{color}">{esc(label)}</text>')
        elif kind in ('line','arrow'):
            points=[(x+px,y+py) for px,py in e['points']]
            coords=' '.join(f'{px:g},{py:g}' for px,py in points)
            parts.append(f'<polyline points="{coords}" {base} stroke-linejoin="round"/>')
            if e.get('endArrowhead'):
                if e['endArrowhead']!='arrow' or e.get('startArrowhead'): raise ValueError('Unsupported arrowhead')
                (ax,ay),(bx,by)=points[-2:]
                angle=math.atan2(by-ay,bx-ax); length=12
                wings=[(bx-length*math.cos(angle+a),by-length*math.sin(angle+a)) for a in [-.5,.5]]
                parts.append(f'<polyline points="{wings[0][0]},{wings[0][1]} {bx},{by} {wings[1][0]},{wings[1][1]}" fill="none" stroke="{color}" stroke-width="{sw}"/>')
        else: raise ValueError(f'Unsupported scene element: {kind}')
    return '\n'.join(parts)+'\n</svg>\n'

def main():
    scenes=sorted((ROOT/'assets/diagrams').glob('*.excalidraw'))
    if not scenes: raise ValueError('No editable scenes found')
    for path in scenes:
        path.with_suffix('.svg').write_text(export(json.loads(path.read_text())),encoding='utf-8')
    print(f'Exported {len(scenes)} self-contained SVG diagrams from editable scenes.')

if __name__=='__main__': main()

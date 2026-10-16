#!/usr/bin/env python3
"""Insert manifested PNG/JPEG comics after JBD v3 scene-point steps, collision-free."""
import argparse, base64, copy, datetime, io, json, math, uuid
from pathlib import Path
from PIL import Image, ImageOps

def overlap(a,b):
    return a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3]

def camera(step):
    t=step['target']
    if t['kind']!='scene-point': raise ValueError('Unsupported target kind; resolve with native adapter')
    v=t.get('referenceViewport',{'width':1280,'height':720}); z=t['zoom']
    if z<=0: raise ValueError('Invalid camera zoom')
    w,h=v['width']/z,v['height']/z; x,y=t['point']['x'],t['point']['y']
    if step.get('fallbackCamera',{}).get('rotation',0): w=h=math.hypot(w,h)
    return t['sceneId'],(x-w/2,y-h/2,x+w/2,y+h/2)

def bounds(n,nodes,seen=None):
    seen=set() if seen is None else seen
    if n['id'] in seen: raise ValueError('Cyclic connector')
    seen=seen|{n['id']}
    if n['type']=='connector':
        c=n['connector']; ends=[nodes[c[k]] for k in ('sourceNodeId','targetNodeId')]
        if any(e['sceneId']!=n['sceneId'] for e in ends): raise ValueError('Cross-scene connector')
        bs=[bounds(e,nodes,seen) for e in ends]
        return min(b[0] for b in bs),min(b[1] for b in bs),max(b[2] for b in bs),max(b[3] for b in bs)
    if n['type'] not in ('text','shape','image','frame'): raise ValueError('Unsupported node type: '+n['type'])
    if n.get('parentId') or n.get('parentNodeId'): raise ValueError('Resolve parent transform before inserting')
    t=n['transform']; x,y=t['x'],t['y']; w=n['width']*t.get('scaleX',1); h=n['height']*t.get('scaleY',1)
    if t.get('rotation',0):
        # Circle about transform origin encloses either center- or corner-rotation conventions.
        r=math.hypot(w,h); return x-r,y-r,x+r,y+r
    return min(x,x+w),min(y,y+h),max(x,x+w),max(y,y+h)


def prepare_image(path, image_format='jpeg', jpeg_quality=90, max_width=1920):
    """Encode an embedding copy; never modify input files."""
    if image_format not in ('jpeg', 'png', 'original'):
        raise ValueError('image_format must be jpeg, png or original')
    if type(jpeg_quality) is not int or not 1 <= jpeg_quality <= 95:
        raise ValueError('jpeg_quality must be an integer from 1 to 95')
    if type(max_width) is not int or max_width <= 0:
        raise ValueError('max_width must be a positive integer')
    data = Path(path).read_bytes()
    with Image.open(io.BytesIO(data)) as check:
        check.verify()
    with Image.open(io.BytesIO(data)) as source:
        fmt = source.format
        mime = {'PNG':'image/png', 'JPEG':'image/jpeg', 'WEBP':'image/webp'}.get(fmt)
        if mime is None:
            raise ValueError('Unsupported image format')
        if getattr(source, 'n_frames', 1) != 1:
            raise ValueError('Comic must be a static image')
        im = ImageOps.exif_transpose(source)
        w, h = im.size
        if abs(w/h-16/9)/(16/9) > .005:
            raise ValueError('Comic must be 16:9 (0.5% tolerance)')
        orientation = source.getexif().get(274, 1)
        if image_format == 'original':
            if orientation != 1:
                raise ValueError('Normalize EXIF orientation before original-byte embedding')
            return data, mime
        if image_format == 'jpeg' and fmt == 'JPEG' and w <= max_width and orientation == 1 and im.mode == 'RGB':
            return data, mime
        if w > max_width:
            im = im.resize((max_width, max(1, round(h*max_width/w))), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        if image_format == 'jpeg':
            rgba = im.convert('RGBA')
            rgb = Image.new('RGB', rgba.size, 'white')
            rgb.paste(rgba, mask=rgba.getchannel('A'))
            rgb.save(output, format='JPEG', quality=jpeg_quality, subsampling=0, optimize=True)
            mime = 'image/jpeg'
        else:
            im.save(output, format='PNG', optimize=True)
            mime = 'image/png'
        encoded = output.getvalue()
    with Image.open(io.BytesIO(encoded)) as check:
        check.verify()
    return encoded, mime

def insert(source,manifest,*,image_format='jpeg',jpeg_quality=90,max_width=1920):
    p=copy.deepcopy(source)
    if p['schemaVersion']!=3: raise ValueError('Only schemaVersion 3 supported')
    steps=p['steps']; ids=[s['id'] for s in steps]
    if len(ids)!=len(set(ids)): raise ValueError('Duplicate source step IDs')
    if [s['order'] for s in steps]!=sorted(s['order'] for s in steps): raise ValueError('Resolve inconsistent source order')
    if any(s['id'].startswith('comic-step-') for s in steps): raise ValueError('Already augmented; use original source')
    occupied={sid:[] for sid in p['scenes']}
    for key,n in p['nodes'].items():
        if key!=n['id']: raise ValueError('Node ID mismatch')
        occupied[n['sceneId']].append(bounds(n,p['nodes']))
    for s in steps:
        sid,b=camera(s);occupied[sid].append(b)
    additions={}; reservations=[]
    if not manifest: raise ValueError('No manifest items')
    for item in manifest:
        anchor=item['anchor_step_id']
        if anchor not in ids: raise ValueError('Unknown anchor: '+anchor)
        anchor_step=steps[ids.index(anchor)]; sid=anchor_step['target']['sceneId']
        data,mime=prepare_image(item['image'],item.get('image_format',image_format),item.get('jpeg_quality',jpeg_quality),item.get('max_width',max_width))
        # Fixed 1280×720 camera plus 32-unit perimeter; dynamically placed below ALL occupied bounds.
        x=anchor_step['target']['point']['x']; top=max([b[3] for b in occupied[sid]] or [0])+160
        y=top+392; rect=(x-672,y-392,x+672,y+392)
        if any(overlap(rect,b) for b in occupied[sid]): raise AssertionError('Placement collision')
        occupied[sid].append(rect);reservations.append((sid,rect))
        token=uuid.uuid4().hex; nid='comic-image-'+token; stid='comic-step-'+token
        p['nodes'][nid]={'id':nid,'type':'image','name':item['title'],'sceneId':sid,'transform':{'x':x-640,'y':y-360,'scaleX':1,'scaleY':1,'rotation':0},'width':1280,'height':720,'zIndex':10,'locked':False,'style':{'fill':'transparent','stroke':'transparent','textColor':'transparent','fontSize':1,'radius':0},'text':item['title'],'image':{'src':'data:'+mime+';base64,'+base64.b64encode(data).decode(),'alt':item['title'],'fit':'contain'}}
        p['scenes'][sid]['nodeIds'].append(nid)
        s={'id':stid,'order':0,'label':'四格漫畫｜'+item['title'],'target':{'kind':'scene-point','sceneId':sid,'point':{'x':x,'y':y},'zoom':1,'referenceViewport':{'width':1280,'height':720}},'durationMs':900,'holdMs':500,'easing':'smooth','speakerNotes':item.get('speaker_notes','依左上、右上、左下、右下閱讀。')}
        additions.setdefault(anchor,[]).append(s)
    p['steps']=[]
    for s in steps:p['steps'].extend([s]+additions.get(s['id'],[]))
    for i,s in enumerate(p['steps']):s['order']=i
    p.setdefault('metadata',{})['updatedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    assert all(p['nodes'][k]==v for k,v in source['nodes'].items())
    assert [s['id'] for s in p['steps'] if s['id'] in ids]==ids
    for anchor,new in additions.items():
        idx=next(i for i,s in enumerate(p['steps']) if s['id']==anchor)
        assert p['steps'][idx+1:idx+1+len(new)]==new
    for sid,scene in p['scenes'].items():
        assert len(scene['nodeIds'])==len(set(scene['nodeIds']))
        assert all(n in p['nodes'] and p['nodes'][n]['sceneId']==sid for n in scene['nodeIds'])
    return p

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('source',type=Path);ap.add_argument('manifest',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--image-format',choices=('jpeg','png','original'),default='jpeg');ap.add_argument('--jpeg-quality',type=int,default=90);ap.add_argument('--max-width',type=int,default=1920);a=ap.parse_args()
    if a.output.exists(): raise ValueError('Output exists; choose a new versioned filename')
    items=json.loads(a.manifest.read_text(encoding='utf-8-sig'))['items']
    for item in items:
        path=Path(item['image']);item['image']=str(path if path.is_absolute() else a.manifest.parent/path)
    source=json.loads(a.source.read_text(encoding='utf-8-sig'))
    p=insert(source,items,image_format=a.image_format,jpeg_quality=a.jpeg_quality,max_width=a.max_width)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    # Exclusive creation avoids clobbering concurrent output.
    with a.output.open('x',encoding='utf-8') as f:json.dump(p,f,ensure_ascii=False,indent=2)
    added=[n for key,n in p['nodes'].items() if key not in source['nodes']]
    original_bytes=sum(Path(item['image']).stat().st_size for item in items)
    embedded_bytes=sum(len(base64.b64decode(n['image']['src'].split(',',1)[1])) for n in added)
    print(json.dumps({'original_image_bytes':original_bytes,'embedded_image_bytes':embedded_bytes,'image_bytes_reduction_percent':round(100*(1-embedded_bytes/original_bytes),2),'output_bytes':a.output.stat().st_size,'visual_quality':'requires_review','output':str(a.output.resolve()),'inserted':len(items),'total_steps':len(p['steps']),'structural_validation':'passed','runtime_import':'not_checked'},ensure_ascii=False))
if __name__=='__main__':main()

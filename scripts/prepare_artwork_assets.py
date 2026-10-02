"""Conservative, non-generative paper cleanup and colour grading.

Original assets remain untouched. Outputs are lossless PNGs at original size.
Run from the repository root. No resampling, sharpening, or generative operations.
"""
from pathlib import Path
import json
import re
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'dist/assets'
M = np.array([[.4124564,.2126729,.0193339],
              [.3575761,.7151522,.1191920],
              [.1804375,.0721750,.9503041]])
WHITE = np.array([.95047, 1., 1.08883])

def rgb_to_lab(rgb):
    v = rgb.astype(np.float32) / 255
    v = np.where(v <= .04045, v / 12.92, ((v + .055) / 1.055) ** 2.4)
    xyz = (v @ M) / WHITE
    f = np.where(xyz > .00885645168, np.cbrt(xyz), xyz * 7.787037 + 16/116)
    return np.stack([116*f[...,1]-16, 500*(f[...,0]-f[...,1]),
                     200*(f[...,1]-f[...,2])], axis=-1)

def lab_to_linear(lab):
    fy = (lab[...,0]+16)/116
    f = np.stack([fy+lab[...,1]/500,fy,fy-lab[...,2]/200],axis=-1)
    xyz = np.where(f > 6/29, f**3, (f-16/116)/7.787037) * WHITE
    return xyz @ np.linalg.inv(M)

def linear_to_rgb(v):
    v = np.clip(v,0,1)
    return np.uint8(np.rint(255*np.where(v<=.0031308,12.92*v,1.055*v**(1/2.4)-.055)))

def paper_field(lab):
    """Fit the pale paper colour field from its dominant neutral cluster."""
    sample = lab[::4,::4]
    l,a,b = sample.transpose(2,0,1)
    candidate = (l>70) & (np.hypot(a,b)<20)
    hist,edges,_ = np.histogram2d(a[candidate],b[candidate],bins=100,
                                range=[[-25,25],[-25,25]])
    ix,iy = np.unravel_index(gaussian_filter(hist,1).argmax(),hist.shape)
    mode = np.array([edges[ix]+.25,edges[iy]+.25])
    seed = (np.hypot(a-mode[0],b-mode[1])<4) & (l>70)
    h,w = lab.shape[:2]
    ys,xs = np.meshgrid(np.arange(0,h,4)/(h-1),np.arange(0,w,4)/(w-1),indexing='ij')
    features = np.stack([np.ones_like(xs),xs,ys,xs*xs,ys*ys,xs*ys],axis=-1)
    coeff = np.linalg.lstsq(features[seed],sample[seed],rcond=None)[0]
    # Retain only stable paper samples for a second fit.
    predicted = features @ coeff
    residual = sample-predicted
    seed &= (np.hypot(residual[...,1],residual[...,2])<3.5) & (abs(residual[...,0])<7)
    coeff = np.linalg.lstsq(features[seed],sample[seed],rcond=None)[0]
    yy,xx = np.meshgrid(np.linspace(0,1,h),np.linspace(0,1,w),indexing='ij')
    full = np.stack([np.ones_like(xx),xx,yy,xx*xx,yy*yy,xx*yy],axis=-1)
    return full @ coeff

def whiten_paper(name):
    src = np.array(Image.open(ASSETS/name).convert('RGB'))
    lab = rgb_to_lab(src)
    field = paper_field(lab)
    chroma_distance = np.hypot(lab[...,1]-field[...,1],lab[...,2]-field[...,2])
    # Pale coloured strokes and dark marks are explicitly excluded.
    safe = (chroma_distance < 5.5) & (lab[...,0]>65) & (lab[...,0]>field[...,0]-8)
    distance = distance_transform_edt(safe)
    # Two source pixels adjacent to coloured marks are preserved verbatim.
    alpha = np.clip((distance-2)/2,0,1)
    alpha = alpha*alpha*(3-2*alpha)
    result = np.uint8(np.rint(src*(1-alpha[...,None])+255*alpha[...,None]))
    name_out = Path(name).stem+'-white.png'
    Image.fromarray(result).save(ASSETS/name_out,optimize=True)
    protected = ~safe | (distance<=2)
    assert np.array_equal(src[protected],result[protected])
    assert np.all(result[alpha==1]==255)
    return name_out, {'size':list(src.shape[:2][::-1]),
        'changed_percent':round(100*np.mean(np.any(result!=src,axis=2)),2),
        'pure_white_percent':round(100*np.mean(np.all(result==255,axis=2)),2),
        'protected_pixels_identical':True}

def grade(name, saturation, pink, warmth):
    src = np.array(Image.open(ASSETS/name).convert('RGB'))
    lab = rgb_to_lab(src)
    target = lab.copy()
    l = lab[...,0]
    weight = np.clip((l-8)/25,0,1)*np.clip((98-l)/15,0,1)
    target[...,1] = lab[...,1]*(1+(saturation-1)*weight)+pink*weight
    target[...,2] = lab[...,2]*(1+(saturation-1)*weight)+warmth*weight
    # Compress only out-of-gamut chroma; never clip channels or alter texture.
    linear = lab_to_linear(target)
    outside = np.any((linear<0)|(linear>1),axis=2)
    if np.any(outside):
        selected = target[outside].copy()
        lo=np.zeros(len(selected));hi=np.ones(len(selected))
        for _ in range(12):
            scale=(lo+hi)/2
            check=selected.copy();check[:,1:]*=scale[:,None]
            rgb=lab_to_linear(check)
            valid=np.all((rgb>=0)&(rgb<=1),axis=1)
            lo=np.where(valid,scale,lo);hi=np.where(valid,hi,scale)
        target[outside,1:]=selected[:,1:]*lo[:,None]
    result = linear_to_rgb(lab_to_linear(target))
    name_out = Path(name).stem+'-graded.png'
    Image.fromarray(result).save(ASSETS/name_out,optimize=True)
    ldiff=np.abs(rgb_to_lab(result)[...,0]-lab[...,0])
    return name_out,{'size':list(src.shape[:2][::-1]),'saturation':saturation,
        'pink_bias':pink,'warmth_bias':warmth,
        'mean_lightness_difference':round(float(ldiff.mean()),4),
        'clipped_channel_fraction':round(float(np.mean((result==0)|(result==255))),5)}

if __name__ == '__main__':
    page=(ROOT/'dist/artwork-sea-to-sun.html').read_text()
    manifest_path=ROOT/'scripts/artwork-asset-manifest.json'
    names=list(json.loads(manifest_path.read_text())['white']) if manifest_path.exists() else list(dict.fromkeys(re.findall(r'assets/(MAG[^"? ]+\.jpg)',page)))
    manifest={'white':{},'grade':{}}
    for name in names:
        # This is the user's blue reference; retain its original file exactly.
        if name=='MAGnH1u2Lzs.jpg':continue
        out,metrics=whiten_paper(name)
        manifest['white'][name]={'output':out,**metrics}
        print('white',name,metrics,flush=True)
    for name,sat,pink,warm in [
        ('MAGnaL6KQ5k.png',1.16,2.0,-1.5),
        ('MAGnaM_BZxQ.png',1.12,2.0,-1.0),
        ('MAGoGIf9-UE.png',1.10,1.5,-1.5),
        ('MAGp-ESWhcU.jpg',1.12,2.5,3.0),
        ('MAGp-FHUqzU.jpg',1.10,2.0,2.5),
    ]:
        out,metrics=grade(name,sat,pink,warm)
        manifest['grade'][name]={'output':out,**metrics}
        print('grade',name,metrics,flush=True)
    (ROOT/'scripts/artwork-asset-manifest.json').write_text(json.dumps(manifest,indent=2))

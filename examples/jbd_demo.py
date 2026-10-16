"""Build a small synthetic JBD v3 deck with the bundled original deckkit."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--course-root',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    output=args.out.resolve()
    if output.exists(): parser.exit(1,'Output already exists; no file overwritten.\n')
    output.parent.mkdir(parents=True,exist_ok=True)
    kit_dir=args.course_root.resolve()/'.agents/skills/view-from-text/tools/deckkit'
    with tempfile.TemporaryDirectory(dir=output.parent) as work:
        assert Path(work).resolve().is_relative_to(output.parent)
        (Path(work)/'figs.json').write_text('{}\n',encoding='utf-8')
        os.environ['DECK_WORK']=work
        os.environ['DECK_PFX']='demo-kp01'
        sys.path.insert(0,str(kit_dir))
        import kit
        u=kit.Unit('u01','虛構示範：梯度下降',0,0)
        u.flow('先定義要改善的量','用損失衡量距離目標有多遠','A loss measures distance from a target',
               '此為轉檔與結構測試。目標在三，先定義損失，再以梯度決定更新方向。數值已驗算。',
               kit.Card('demo-loss',kit.T(r'$L(w)=(w-3)^2$',kit.en('The target is three; the squared distance is the loss.')),c=kit.MAIN,size=28,h=120))
        u.flow('再計算更新','梯度指出目前斜率','The gradient describes the current slope',
               '在零的位置梯度為負六；學習率四分之一，向反方向更新得到一點五，損失由九降到二點二五。',
               kit.Card('demo-update',kit.T(r'$w_0=0,\quad g(w_0)=-6,\quad \eta=0.25,\quad w_1=1.5$',kit.en('One update reduces the loss from nine to two point two five.')),c=kit.REF,size=24,h=150))
        doc=kit.assemble([u],'Synthetic JBD example',[],{'x':200,'y':100,'zoom':1.2,'rotation':0})
        kit.steps[0]['speakerNotes']='教材程度:大學生(undergrad)。本檔為合成格式測試，不代表正式教材驗收。'
        doc['steps']=kit.steps
        with output.open('x',encoding='utf-8') as stream:
            json.dump(doc,stream,ensure_ascii=False,indent=2)
    print(f'Created JBD v3 fixture: {output}')


if __name__=='__main__':
    main()

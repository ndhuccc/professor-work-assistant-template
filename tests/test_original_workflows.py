"""Exercise the original tools from a newly created, synthetic course workspace."""
import base64
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent.parent


def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py')
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def command(*args,cwd=None,env=None):
    result=subprocess.run([sys.executable,*map(str,args)],cwd=cwd,capture_output=True,
                          text=True,encoding='utf-8',errors='replace',env=env,timeout=45)
    if result.returncode:
        raise AssertionError(result.stdout+'\n'+result.stderr)
    return result


class OriginalWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=(ROOT/'workspace/original-workflow-tests').resolve()
        cls.base.mkdir(parents=True,exist_ok=True)
        cls.temp=tempfile.TemporaryDirectory(dir=cls.base)
        assert Path(cls.temp.name).resolve().is_relative_to(cls.base)
        cls.course=module('create_course').create_course(ROOT,Path(cls.temp.name)/'course',
            'DEMO','Synthetic demo','https://example.invalid/demo/',True)
        cls.generated=cls.course/'assignments/labtube-import/assignments_hw01.json'
        command(cls.course/'.agents/skills/assignment-design/build_labtube_import.py','hw01','--course','DEMO',cwd=cls.course)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_original_bundle_hashes(self):
        errors,count=module('verify_bundle').verify(ROOT)
        self.assertEqual(errors,[])
        self.assertGreaterEqual(count,340)

    def test_all_original_course_dependencies_are_copied(self):
        for slug in module('create_course').SKILLS:
            self.assertTrue((self.course/'.agents/skills'/slug/'SKILL.md').is_file())
        for path in ('scripts/check_slides.py','slides/FORMATS.md','requirements-lecture.txt',
                     '.agents/skills/view-from-text/AI_AGENT_FILE_FORMAT_SPEC.md',
                     '.agents/skills/LEVELS.md'):
            self.assertTrue((self.course/path).is_file(),path)

    def test_course_creation_never_overwrites(self):
        with self.assertRaisesRegex(ValueError,'already exists'):
            module('create_course').create_course(ROOT,self.course,'DEMO','x','')

    def test_markdown_assignment_import_roundtrip(self):
        doc=json.loads(self.generated.read_text(encoding='utf-8'))
        self.assertEqual(doc['schema'],'labtube.assignments.v1')
        self.assertEqual(doc['course'],'DEMO')
        entry=doc['assignments'][0]
        self.assertEqual(entry['code'],'hw01')
        self.assertGreaterEqual(len(entry['details']['sections']),3)
        errors,warnings=module('validate_labtube').validate(doc,course='DEMO')
        self.assertEqual(errors,[])

    def test_quiz_contract_rejects_answer_keys(self):
        doc={'schema':'labtube.quiz.v1','assignment':'hw01','students':[{'student_id':'DEMO-ONLY',
             'questions':[dict(idx=i,qtype=q,prompt='Explain this snippet.',snippet='value = 1',snippet_source='demo.py:1')
                          for i,q in enumerate(('explain','change','reason'),1)]}]}
        validator=module('validate_labtube')
        self.assertEqual(validator.validate(doc)[0],[])
        doc['students'][0]['questions'][0]['answer']='forbidden'
        self.assertTrue(validator.validate(doc)[0])

    def test_local_grades_are_not_claimed_server_verified(self):
        doc={'schema':'labtube.grades.v1','assignment':'hw01','grades':[
             {'student_id':'DEMO-ONLY','idx':1,'score':2,'rationale':'Synthetic test only','needs_review':False}]}
        errors,warnings=module('validate_labtube').validate(doc)
        self.assertEqual(errors,[])
        self.assertTrue(any('server' in w for w in warnings))

    def test_original_jbd_generator_and_validator(self):
        # Use the author's supplied example; never touch student code or a live site.
        script=Path(self.temp.name)/'example_deck.py'
        script.write_bytes((ROOT/'examples/jbd_demo.py').read_bytes())
        env=dict(os.environ,PYTHONUTF8='1')
        draft=script.parent/'draft.jbd.json'
        command(script,'--course-root',self.course,'--out',draft,cwd=script.parent,env=env)
        doc=json.loads(draft.read_text(encoding='utf-8'))
        self.assertEqual(doc['schemaVersion'],3)
        self.assertGreater(len(doc['steps']),1)
        command(self.course/'scripts/check_slides.py',draft,cwd=self.course,env=env)

    @unittest.skipUnless(importlib.util.find_spec('PIL'),'Pillow not installed')
    def test_jpeg_comic_insertion_preserves_original(self):
        from PIL import Image
        script=self.course/'.agents/skills/slides-to-four-panel-comics/scripts/insert_jbd_comics.py'
        spec=importlib.util.spec_from_file_location('comic_insert',script)
        tool=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        # Neutral test bitmap, not a generated comic or user image edit.
        image=Path(self.temp.name)/'neutral-fixture.png'
        Image.new('RGB',(1600,900),'white').save(image)
        node={'id':'n','type':'text','sceneId':'s','transform':{'x':0,'y':0},'width':100,'height':100}
        step={'id':'original','order':0,'target':{'kind':'scene-point','sceneId':'s','point':{'x':50,'y':50},'zoom':1,'referenceViewport':{'width':1280,'height':720}}}
        source={'schemaVersion':3,'scenes':{'s':{'id':'s','nodeIds':['n']}},'nodes':{'n':node},'steps':[step]}
        before=json.dumps(source,sort_keys=True)
        result=tool.insert(source,[{'anchor_step_id':'original','title':'fixture','image':str(image)}])
        doc=result[0] if isinstance(result,tuple) else result
        self.assertEqual(json.dumps(source,sort_keys=True),before)
        self.assertEqual(doc['steps'][0]['id'],'original')
        self.assertEqual(len(doc['steps']),2)
        comic=next(n for n in doc['nodes'].values() if n['type']=='image')
        prefix,encoded=comic['image']['src'].split(',',1)
        self.assertEqual(prefix,'data:image/jpeg;base64')
        with Image.open(io.BytesIO(base64.b64decode(encoded))) as check:
            self.assertEqual(check.format,'JPEG')
        self.assertFalse(tool.overlap(tool.camera(doc['steps'][0])[1],tool.camera(doc['steps'][1])[1]))


if __name__=='__main__':
    unittest.main()

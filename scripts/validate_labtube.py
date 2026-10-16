"""Validate a local exchange file with the bundled original LabTube contracts.

Offline validation is structural. Real enrollment, answer keys, accepted SHAs and
locked grades must be revalidated by the target LabTube server before import.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
UPSTREAM=ROOT/'integrations/labtube/upstream'


def validate(doc, assignment='hw01', course='DEMO', rubric_max=100):
    if not isinstance(doc, dict):
        return ['Root must be a JSON object'],[]
    sys.path.insert(0,str(UPSTREAM))
    try:
        from services import contracts as c
        schema=doc.get('schema')
        warnings=[]
        if schema==c.ASSIGNMENTS_SCHEMA:
            _,errors=c.validate_assignments(doc,course)
        elif schema==c.QUIZ_SCHEMA:
            _,errors,warnings=c.validate_quiz(doc,assignment)
            warnings.append('Enrollment is not checked offline')
        elif schema==c.ANSWERS_SCHEMA:
            errors=c.validate_answers_doc(doc)
        elif schema==c.GRADES_SCHEMA:
            keys={(g.get('student_id'),g.get('idx')) for g in doc.get('grades',[]) if isinstance(g,dict)}
            _,errors=c.validate_grades(doc,assignment,keys)
            warnings.append('Answer existence and finalized status must be checked by the server')
        elif schema==c.RUBRIC_SCHEMA:
            _,errors=c.validate_rubric(doc,assignment,rubric_max)
            warnings.append('Enrollment and evaluated_sha must be checked against registered submissions')
        elif schema==c.REPOCHECK_SCHEMA:
            repos=doc.get('repos')
            if not isinstance(repos,list):
                return ['repos must be an array'],[]
            registered={r.get('student_id'):r.get('repo') for r in repos if isinstance(r,dict)}
            _,_,_,errors=c.validate_repocheck(doc,assignment,registered)
            warnings.append('Registered repos and paths must be checked against the target course')
        else:
            errors=['Unsupported schema: '+str(schema)]
        return errors,warnings
    except (TypeError,AttributeError,KeyError,ValueError) as e:
        return ['Malformed exchange file: '+str(e)],[]
    finally:
        sys.path.pop(0)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('file',type=Path)
    p.add_argument('--assignment',default='hw01')
    p.add_argument('--course',default='DEMO')
    p.add_argument('--rubric-max',type=int,default=100)
    args=p.parse_args()
    try:
        data=json.loads(args.file.read_text(encoding='utf-8-sig'))
        errors,warnings=validate(data,args.assignment,args.course,args.rubric_max)
    except (OSError,ValueError) as e:
        errors,warnings=[str(e)],[]
    for warning in warnings: print('WARN: '+warning)
    for error in errors: print('FAIL: '+error)
    if not errors: print('PASS: local contract validation; no external import performed')
    return int(bool(errors))


if __name__=='__main__':
    raise SystemExit(main())

import time
import yaml
import copy
from dataclasses import dataclass
from typing import Dict, List, Tuple
from pydantic import ValidationError

import helper
from logger import logger
from steps import StepItems


class InvalidYAMLSyntax(SyntaxError):
    """ Exception to raise if settings yaml syntax is not right """


class MethodFieldMissingException(KeyError):
    """ Exception when field `method` not found in step """


class ArgsValidationException(ValidationError):
    """ Exception when validate_arguments fails """


class MethodInvalidException(AttributeError):
    """ Exception when the passed method in a step in not valid """


@dataclass
class Job:
    steps: List[Dict]
    allowed_methods: Tuple = tuple([k for k, v in vars(StepItems).items() if isinstance(v, classmethod)])

    def __post_init__(self):
        steps = copy.deepcopy(self.steps)
        for index, step_args in enumerate(steps):
            logger.info(f' -----------------------------  Validation: Step #{index} ----------------------------- ')
            try:
                method = step_args.pop('method')
            except KeyError:
                logger.error(f'❌ Field method not found in step args {step_args}')
                raise MethodFieldMissingException(f'❌ Field method not found in step args {step_args}')

            if method not in self.allowed_methods:
                raise MethodInvalidException(f'❌ Method {method} not in allowed methods: {self.allowed_methods}')

            logger.info(f'🙌 Method: `{method}` Current step args: {step_args}')
            # Important to set `cls` here, else `validate` cannot read classmethods
            step_args['cls'] = StepItems
            for k, v in step_args.copy().items():
                if k in ['inputs', 'on_always']:
                    try:
                        step_args[k] = getattr(helper, v['method'])
                        self.steps[index][k] = getattr(helper, v['method'])
                        step_args[f'{k}_args'] = v.get('kwargs', {})
                        self.steps[index][f'{k}_args'] = v.get('kwargs', {})
                    except KeyError:
                        logger.error(f'❌ `inputs` & `on_always` needs a key: `method` for invocation')
                        raise
                    except AttributeError:
                        logger.error(f'❌ Couldn\'t find function {v} in helper')
                        raise
                if k == 'sleep_time':
                    step_args.pop('sleep_time')

            try:
                getattr(StepItems, method).validate(**step_args)
            except AttributeError:
                raise MethodInvalidException(f'❌ Method {method} not in allowed methods: {self.allowed_methods}')
            except ValidationError as e:
                logger.error(e.errors())
                raise

    def __call__(self):
        for index, step_args in enumerate(self.steps):
            method = step_args.pop('method')
            logger.info(f' ----------------------------- Execution: Step #{index}  ----------------------------- ')
            logger.info(f'🙌 Method: `{method}` Current step args: {step_args}')
            try:
                if 'sleep_time' in step_args:
                    sleep_time = step_args.pop('sleep_time')
                    logger.info(f'🤔 Asked to sleep for {sleep_time} secs. Sleeping 😴')
                    time.sleep(sleep_time)
                getattr(StepItems, method)(**step_args)
            except Exception as e:
                logger.error(e)
                raise


def main():
    with open('settings.yaml') as f:
        settings = yaml.safe_load(f)

    if 'jobs' not in settings:
        raise InvalidYAMLSyntax('Field `jobs` not found in the yaml')

    # TODO: Handle concurrent jobs execution, or add sleep time b/w sequence of jobs?
    for job_name in settings['jobs'].keys():
        if 'steps' not in settings['jobs'][job_name]:
            raise InvalidYAMLSyntax('Field `steps` not found in the job')
        job = Job(steps=settings['jobs'][job_name]['steps'])
        job()


if __name__ == '__main__':
    main()

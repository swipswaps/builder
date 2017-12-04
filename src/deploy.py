"""module concerns itself with tasks involving branch deployments of projects."""

from fabric.api import task
from decorators import requires_aws_stack
from buildercore import bootstrap
from buildercore.concurrency import concurrency_for
import buildvars

import logging

LOG = logging.getLogger(__name__)

@task
@requires_aws_stack
def switch_revision_update_instance(stackname, revision=None, concurrency='serial'):
    buildvars.switch_revision(stackname, revision)
    bootstrap.update_stack(stackname, concurrency=concurrency_for(stackname, concurrency))

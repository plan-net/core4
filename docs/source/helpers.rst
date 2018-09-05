#######
helpers
#######

Helpers provide additional functionality to a CoreJob as a Mixin.
This is the goto place for adding new new central Methods each Job should be provided with.


helper configuration
====================

Helpers are Mixins that inherit from CoreBase.
They do therfore have access to the configuration and logging.

.. code-block:: python

    class FunctionMixin(CoreBase):
        def add_and_mul(self, a , b,c)
            return (a + b) * c


All Jobs that want to use these helpers have to inherit from them:

.. code-block:: python

    class CustomJob(CoreJob, FunctionMixin):
        def execute(self)
            # The Mixin-function is now available under "self"
            self.function(a=2,b=3,c=4)

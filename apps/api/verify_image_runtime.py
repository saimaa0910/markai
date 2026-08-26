from unittest.mock import MagicMock
from api.ai.agents.image.router import _get_available_image_providers, _get_available_image_models
from api.ai.agents.image.executor import ImageExecutor
import uuid

class FakeQuery:
    def __init__(self, result):
        self._result = result
    def all(self):
        return self._result
    def filter(self, *args, **kwargs):
        return self

class FakeDB:
    def query(self, model):
        if model.__name__ == 'AIProvider':
            return FakeQuery([])
        if model.__name__ == 'AIModelRegistry':
            return FakeQuery([])
        return FakeQuery([])

providers = _get_available_image_providers(FakeDB())
models = _get_available_image_models(FakeDB())
print('providers', [p['name'] for p in providers[:5]])
print('models', [m['name'] for m in models])

executor = ImageExecutor(MagicMock(), uuid.uuid4(), uuid.uuid4())
executor.provider_router = MagicMock()
executor.provider_router.generate_image.side_effect = RuntimeError('No supported image providers')
result = executor.generate(prompt='A modern product mockup', style='minimal')
print(result['status'], result['error']['code'], result['error']['message'])

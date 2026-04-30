import pytest
from unittest.mock import MagicMock
from services.memory_injector import MemoryInjector


@pytest.fixture
def memory_injector(mock_vector_store, mock_ollama, mock_config):
    return MemoryInjector(mock_vector_store, mock_ollama, mock_config)


class TestInject:
    def test_inject_returns_none_when_no_memories_found(self, memory_injector, mock_vector_store):
        mock_vector_store.client.search.return_value = []
        result = memory_injector.inject(query='test query', platform='test')
        assert result is None

    def test_inject_returns_dict_when_memories_found(self, memory_injector, mock_vector_store):
        mock_vector_store.client.search.return_value = [
            MagicMock(score=0.85, payload={'content': 'test memory', 'type': 'preference', 'dimensions': {}})
        ]
        result = memory_injector.inject(query='test query', platform='test')
        assert result is not None
        assert 'injected_messages' in result
        assert 'context' in result
        assert 'memories_found' in result
        assert result['memories_found'] == 1

    def test_inject_with_custom_recall_count_and_threshold(self, memory_injector, mock_vector_store, mock_ollama):
        mock_vector_store.client.search.return_value = []
        memory_injector.inject(query='test', platform='test', recall_count=10, similarity_threshold=0.5, injection_position='system')
        mock_ollama.embed.assert_called_once_with('test')
        mock_vector_store.client.search.assert_called_once()

    def test_inject_filters_low_score_memories(self, memory_injector, mock_vector_store):
        mock_vector_store.client.search.return_value = [
            MagicMock(score=0.9, payload={'content': 'high score', 'type': 'preference', 'dimensions': {}}),
            MagicMock(score=0.5, payload={'content': 'low score', 'type': 'preference', 'dimensions': {}}),
        ]
        result = memory_injector.inject(query='test', platform='test', similarity_threshold=0.7)
        assert result['memories_found'] == 1
        assert 'high score' in result['context']


class TestSearchMemories:
    def test_search_memories_success(self, memory_injector, mock_vector_store, mock_ollama):
        mock_vector_store.client.search.return_value = [
            MagicMock(score=0.85, payload={'content': 'memory content', 'type': 'preference', 'dimensions': {'key': 'value'}})
        ]
        memories = memory_injector._search_memories('test query', recall_count=5, similarity_threshold=0.7)
        assert len(memories) == 1
        assert memories[0]['content'] == 'memory content'
        assert memories[0]['type'] == 'preference'
        assert memories[0]['dimensions'] == {'key': 'value'}
        assert memories[0]['score'] == 0.85

    def test_search_memories_exception(self, memory_injector, mock_vector_store, mock_ollama, capsys):
        mock_ollama.embed.side_effect = Exception('embed error')
        memories = memory_injector._search_memories('test', recall_count=5, similarity_threshold=0.7)
        assert memories == []

    def test_search_memories_multiple_results_filtered(self, memory_injector, mock_vector_store):
        mock_vector_store.client.search.return_value = [
            MagicMock(score=0.9, payload={'content': 'high', 'type': 'preference', 'dimensions': {}}),
            MagicMock(score=0.8, payload={'content': 'medium', 'type': 'preference', 'dimensions': {}}),
            MagicMock(score=0.5, payload={'content': 'low', 'type': 'preference', 'dimensions': {}}),
        ]
        memories = memory_injector._search_memories('test', recall_count=5, similarity_threshold=0.75)
        assert len(memories) == 2
        assert all(m['score'] >= 0.75 for m in memories)


class TestBuildContextString:
    def test_build_context_string_empty(self, memory_injector):
        result = memory_injector._build_context_string([])
        assert result == ''

    def test_build_context_string_single_memory(self, memory_injector):
        memories = [{'content': 'I prefer dark mode', 'type': 'preference', 'score': 0.9}]
        result = memory_injector._build_context_string(memories)
        assert '记忆上下文' in result
        assert '偏好习惯' in result
        assert 'I prefer dark mode' in result

    def test_build_context_string_multiple_types(self, memory_injector):
        memories = [
            {'content': 'likes Python', 'type': 'preference', 'score': 0.9},
            {'content': 'expert in ML', 'type': 'expertise', 'score': 0.85},
            {'content': 'working on backend', 'type': 'project_context', 'score': 0.8},
        ]
        result = memory_injector._build_context_string(memories)
        assert '偏好习惯' in result
        assert '专业知识' in result
        assert '项目上下文' in result
        assert 'likes Python' in result
        assert 'expert in ML' in result
        assert 'working on backend' in result

    def test_build_context_string_unknown_type(self, memory_injector):
        memories = [{'content': 'some fact', 'type': 'custom_type', 'score': 0.9}]
        result = memory_injector._build_context_string(memories)
        assert 'custom_type' in result
        assert 'some fact' in result

    def test_build_context_string_multiple_same_type(self, memory_injector):
        memories = [
            {'content': 'fact 1', 'type': 'preference', 'score': 0.9},
            {'content': 'fact 2', 'type': 'preference', 'score': 0.85},
        ]
        result = memory_injector._build_context_string(memories)
        assert result.count('偏好习惯') == 1
        assert 'fact 1' in result
        assert 'fact 2' in result

    def test_build_context_string_missing_type_key(self, memory_injector):
        memories = [{'content': 'content without type', 'score': 0.9}]
        result = memory_injector._build_context_string(memories)
        assert 'unknown' in result
        assert 'content without type' in result


class TestBuildInjectedMessages:
    def test_build_injected_messages_system_position(self, memory_injector):
        messages = memory_injector._build_injected_messages(query='test query', context='test context', position='system')
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[0]['content'] == 'test context'
        assert messages[1]['role'] == 'user'
        assert messages[1]['content'] == 'test query'

    def test_build_injected_messages_other_position(self, memory_injector):
        messages = memory_injector._build_injected_messages(query='test query', context='test context', position='user')
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[0]['content'] == 'test context'
        assert messages[1]['role'] == 'user'
        assert messages[1]['content'] == 'test query'

    def test_build_injected_messages_empty_context(self, memory_injector):
        messages = memory_injector._build_injected_messages(query='test query', context='', position='system')
        assert len(messages) == 2
        assert messages[0]['content'] == ''
        assert messages[1]['content'] == 'test query'


class TestMemoryInjectorInit:
    def test_init_sets_attributes(self, memory_injector, mock_vector_store, mock_ollama, mock_config):
        assert memory_injector.vector_store is mock_vector_store
        assert memory_injector.ollama is mock_ollama
        assert memory_injector.config is mock_config
        assert memory_injector.collection_name == 'memories'

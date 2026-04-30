from unittest.mock import patch, MagicMock
from datetime import datetime
from uuid import uuid4
import pytest

from services.profile_manager import ProfileManager, Profile


class TestProfileManagerCreateProfile:
    """Test create_profile method"""

    @patch('services.profile_manager.uuid4')
    @patch('services.profile_manager.datetime')
    def test_create_profile_success(self, mock_datetime, mock_uuid):
        """Test creating a profile successfully"""
        mock_uuid.return_value = 'test-uuid-1234'
        mock_datetime.now.return_value = datetime(2026, 4, 30, 12, 0, 0)

        manager = ProfileManager()
        profile = manager.create_profile()

        assert profile.profile_id == 'test-uuid-1234'
        assert profile.dimensions == {}
        assert profile.summary == ""
        assert profile.updated_at == datetime(2026, 4, 30, 12, 0, 0)
        assert 'test-uuid-1234' in manager._profiles

    @patch('services.profile_manager.uuid4')
    @patch('services.profile_manager.datetime')
    def test_create_profile_stores_in_profiles_dict(self, mock_datetime, mock_uuid):
        """Test that created profile is stored in internal dict"""
        mock_uuid.return_value = 'test-uuid-5678'
        mock_datetime.now.return_value = datetime(2026, 4, 30, 12, 0, 0)

        manager = ProfileManager()
        profile = manager.create_profile()

        assert manager._profiles['test-uuid-5678'] == profile


class TestProfileManagerGetProfile:
    """Test get_profile method"""

    def test_get_profile_found(self):
        """Test getting an existing profile"""
        manager = ProfileManager()
        profile = Profile(
            profile_id='existing-id',
            dimensions={'test': []},
            summary="test summary",
            updated_at=datetime.now()
        )
        manager._profiles['existing-id'] = profile

        result = manager.get_profile('existing-id')

        assert result == profile
        assert result.profile_id == 'existing-id'

    def test_get_profile_not_found(self):
        """Test getting a non-existent profile returns None"""
        manager = ProfileManager()

        result = manager.get_profile('non-existent-id')

        assert result is None


class TestProfileManagerUpdateProfile:
    """Test update_profile method"""

    @patch('services.profile_manager.datetime')
    def test_update_profile_new_dimension(self, mock_datetime):
        """Test updating profile with a new dimension"""
        mock_datetime.now.return_value = datetime(2026, 4, 30, 12, 0, 0)

        manager = ProfileManager()
        profile = Profile(
            profile_id='test-id',
            dimensions={},
            summary="",
            updated_at=datetime.now()
        )
        manager._profiles['test-id'] = profile

        result = manager.update_profile('test-id', 'interest', {'topic': 'AI'})

        assert result == profile
        assert 'interest' in result.dimensions
        assert len(result.dimensions['interest']) == 1
        assert result.dimensions['interest'][0]['data'] == {'topic': 'AI'}
        assert result.dimensions['interest'][0]['updated_at'] == '2026-04-30T12:00:00'

    @patch('services.profile_manager.datetime')
    def test_update_profile_existing_dimension(self, mock_datetime):
        """Test updating profile with an existing dimension appends data"""
        mock_datetime.now.side_effect = [
            datetime(2026, 4, 30, 12, 0, 0),
            datetime(2026, 4, 30, 13, 0, 0)
        ]

        manager = ProfileManager()
        profile = Profile(
            profile_id='test-id',
            dimensions={'interest': [{'data': {'old': 'data'}, 'updated_at': '2026-04-30T11:00:00'}]},
            summary="",
            updated_at=datetime.now()
        )
        manager._profiles['test-id'] = profile

        result = manager.update_profile('test-id', 'interest', {'topic': 'ML'})

        assert len(result.dimensions['interest']) == 2
        assert result.dimensions['interest'][1]['data'] == {'topic': 'ML'}

    def test_update_profile_not_found(self):
        """Test updating non-existent profile raises ValueError"""
        manager = ProfileManager()

        with pytest.raises(ValueError, match="Profile not found: unknown-id"):
            manager.update_profile('unknown-id', 'dimension', {})


class TestProfileManagerMergeMemories:
    """Test merge_memories method"""

    @patch('services.profile_manager.datetime')
    def test_merge_memories_success(self, mock_datetime):
        """Test merging memories into profile"""
        mock_datetime.now.side_effect = [
            datetime(2026, 4, 30, 12, 0, 0),
            datetime(2026, 4, 30, 13, 0, 0),
            datetime(2026, 4, 30, 14, 0, 0),
            datetime(2026, 4, 30, 15, 0, 0),
            datetime(2026, 4, 30, 16, 0, 0),
        ]

        manager = ProfileManager()
        profile = Profile(
            profile_id='test-id',
            dimensions={},
            summary="",
            updated_at=datetime.now()
        )
        manager._profiles['test-id'] = profile

        memories = {
            'interest': {'data': {'topic': 'AI'}},
            'skill': {'data': {'level': 'advanced'}}
        }

        result = manager.merge_memories('test-id', memories)

        assert result == profile
        assert 'interest' in result.dimensions
        assert 'skill' in result.dimensions

    @patch('services.profile_manager.datetime')
    def test_merge_memories_with_error_in_data(self, mock_datetime):
        """Test merging memories when data contains error key"""
        mock_datetime.now.return_value = datetime(2026, 4, 30, 12, 0, 0)

        manager = ProfileManager()
        profile = Profile(
            profile_id='test-id',
            dimensions={},
            summary="",
            updated_at=datetime.now()
        )
        manager._profiles['test-id'] = profile

        memories = {
            'bad_data': {'data': {'error': 'some error'}}
        }

        result = manager.merge_memories('test-id', memories)

        assert result == profile
        assert 'bad_data' not in result.dimensions

    @patch('services.profile_manager.datetime')
    def test_merge_memories_without_data_key(self, mock_datetime):
        """Test merging memories when memory_data has no data key"""
        mock_datetime.now.return_value = datetime(2026, 4, 30, 12, 0, 0)

        manager = ProfileManager()
        profile = Profile(
            profile_id='test-id',
            dimensions={},
            summary="",
            updated_at=datetime.now()
        )
        manager._profiles['test-id'] = profile

        memories = {
            'no_data': {'other': 'value'}
        }

        result = manager.merge_memories('test-id', memories)

        assert result == profile
        assert 'no_data' not in result.dimensions

    def test_merge_memories_profile_not_found(self):
        """Test merging memories to non-existent profile raises ValueError"""
        manager = ProfileManager()

        with pytest.raises(ValueError, match="Profile not found: unknown-id"):
            manager.merge_memories('unknown-id', {})


class TestProfileManagerGetProfileSummary:
    """Test get_profile_summary method"""

    def test_get_profile_summary_found(self):
        """Test getting summary of existing profile"""
        manager = ProfileManager()
        profile = Profile(
            profile_id='test-id',
            dimensions={},
            summary="Test summary content",
            updated_at=datetime.now()
        )
        manager._profiles['test-id'] = profile

        result = manager.get_profile_summary('test-id')

        assert result == "Test summary content"

    def test_get_profile_summary_not_found(self):
        """Test getting summary of non-existent profile returns empty string"""
        manager = ProfileManager()

        result = manager.get_profile_summary('non-existent-id')

        assert result == ""

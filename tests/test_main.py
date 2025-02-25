import io
import pytest
from unittest.mock import MagicMock, patch
import argparse
from datetime import date

from main import parse_arguments, get_config, run_parish


class TestParseArguments:
    def test_parse_arguments_default(self):
        # Test with no arguments
        with patch('sys.argv', ['main.py']):
            args = parse_arguments()
            assert args.dry_run is False
            assert args.all is False
            assert args.verbose is False
            assert args.mass is False
            assert args.confession is False
            assert args.adoration is False
            assert args.parish_ids == []
    
    def test_parse_arguments_with_options(self):
        # Test with options
        with patch('sys.argv', ['main.py', '-d', '-v', '-m', '-c', '-e', '-a', '1234', '5678']):
            args = parse_arguments()
            assert args.dry_run is True
            assert args.all is True
            assert args.verbose is True
            assert args.mass is True
            assert args.confession is True
            assert args.adoration is True
            assert args.parish_ids == ['1234', '5678']


class TestGetConfig:
    @patch('os.environ', {
        'OPENAI_API_KEY': 'test_key',
        'BULLETIN_ASSISTANT_ID': 'test_assistant',
        'NOTION_API_KEY': 'test_notion',
        'PARISH_DB_ID': 'test_parish_db'
    })
    def test_get_config_all_vars_present(self):
        config = get_config()
        assert config.openai_api_key == 'test_key'
        assert config.bulletin_assistant_id == 'test_assistant'
        assert config.notion_api_key == 'test_notion'
        assert config.parish_db_id == 'test_parish_db'
    
    @patch('os.environ', {
        'OPENAI_API_KEY': 'test_key',
        'BULLETIN_ASSISTANT_ID': 'test_assistant'
    })
    def test_get_config_missing_vars(self):
        with pytest.raises(SystemExit):
            get_config()


@patch('main.get_times')
@patch('main.count_pages')
@patch('main.download_bulletin')
class TestRunParish:
    def test_run_parish_mass_only(self, mock_download, mock_count, mock_get_times):
        # Setup
        mock_download.return_value = "https://example.com/bulletin.pdf"
        mock_count.return_value = 5
        mock_get_times.return_value = (
            [MagicMock(day="Sunday", time=1000)], 
            [], 
            []
        )
        
        config = argparse.Namespace(
            parish_db_id="test_db_id",
            openai_api_key="test_key"
        )
        
        # Execute
        with patch('main.upload_parish_analysis') as mock_upload:
            with patch('main.get_notion_client_from_environment') as mock_notion:
                mock_notion.return_value = MagicMock()
                run_parish("123", "Parishes Online", config, mass=True, confession=False, adoration=False)
        
        # Verify
        assert mock_download.called
        assert mock_count.called
        assert mock_get_times.called
        assert "mass" in mock_get_times.call_args[0][1]
        assert "conf" not in mock_get_times.call_args[0][1]
        assert "adore" not in mock_get_times.call_args[0][1]
    
    def test_run_parish_dry_run(self, mock_download, mock_count, mock_get_times):
        # Setup
        mock_download.return_value = "https://example.com/bulletin.pdf"
        mock_count.return_value = 5
        mock_get_times.return_value = (
            [MagicMock(day="Sunday", time=1000)], 
            [], 
            []
        )
        
        config = argparse.Namespace(
            parish_db_id="test_db_id",
            openai_api_key="test_key"
        )
        
        # Execute
        with patch('main.upload_parish_analysis') as mock_upload:
            with patch('main.get_notion_client_from_environment') as mock_notion:
                mock_notion.return_value = MagicMock()
                run_parish("123", "Parishes Online", config, mass=True, dry_run=True)
        
        # Verify
        assert mock_download.called
        assert mock_count.called
        assert mock_get_times.called
        assert not mock_upload.called  # Should not upload in dry run
        assert not mock_notion.called  # Should not get client in dry run


@patch('main.run_parish')
@patch('main.get_all_parishes')
@patch('main.get_individual_parish')
class TestMain:
    @patch('main.get_notion_client_from_environment')
    @patch('main.get_config')
    @patch('main.parse_arguments')
    def test_main_with_all_flag(self, mock_parse, mock_config, mock_notion, mock_get_individual, mock_get_all, mock_run_parish):
        # Setup
        args = argparse.Namespace(
            all=True,
            dry_run=False,
            mass=True,
            confession=False,
            adoration=False,
            verbose=False,
            parish_ids=[]
        )
        mock_parse.return_value = args
        
        config = MagicMock()
        mock_config.return_value = config
        
        notion_client = MagicMock()
        mock_notion.return_value = notion_client
        
        # Mock parishes
        parish1 = MagicMock(parish_id="123", enabled=True, publisher="Parishes Online", last_run_timestamp=date(2020, 1, 1))
        parish2 = MagicMock(parish_id="456", enabled=True, publisher="Discover Mass", last_run_timestamp=date(2020, 1, 1))
        mock_get_all.return_value = [parish1, parish2]
        
        # Import the function we want to test
        from main import main
        
        # Execute
        with patch('sys.exit'):  # Prevent the test from actually exiting
            main()
        
        # Verify
        assert mock_parse.called
        assert mock_config.called
        assert mock_notion.called
        assert mock_get_all.called
        assert mock_run_parish.call_count == 2
"""
Test file for the track function from shadow_utils.py

This test file covers the track functionality including:
- Pool data retrieval from JSON state
- Settings loading and application
- Price monitoring and threshold detection
- Automatic rebalancing workflow
- Continuous tracking loop
"""

import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch, call
from utils.shadow_utils import Shadow
from models.pool import Pool
from utils.state import save_state, load_state


class TestTrack:
    """Test class for the track function"""
    
    @pytest.fixture
    def mock_browser(self):
        """Create a mock browser for testing"""
        browser = MagicMock()
        browser.pages = [MagicMock(), MagicMock()]  # Mock active pages
        return browser
    
    @pytest.fixture
    def shadow_instance(self, mock_browser):
        """Create a Shadow instance with mock browser"""
        return Shadow(mock_browser)
    
    @pytest.fixture
    def mock_shadow_page(self):
        """Create a mock shadow page with UI elements"""
        page = AsyncMock()
        page.goto = AsyncMock()
        page.locator = MagicMock(return_value=AsyncMock())
        page.click = AsyncMock()
        
        # Mock text content for token information
        locator_with_text = AsyncMock()
        locator_with_text.text_content.return_value = "SHADOW\u2002100\u2002SOL"
        locator_with_text.nth.return_value = AsyncMock()
        locator_with_text.nth.return_value.text_content.return_value = "Available: 50.5"
        
        page.locator.return_value = locator_with_text
        return page
    
    @pytest.fixture
    def sample_pool_data(self):
        """Create sample pool data"""
        return {
            "link": "https://www.shadow.so/liquidity/test-pool-1",
            "range": "wide",
            "token": "SHADOW",
            "amount": 100,
            "upper_range": 1.5,
            "lower_range": 0.5,
            "owner_chat_id": 12345,
            "last_status": "active",
            "meta": {}
        }
    
    @pytest.fixture
    def sample_state(self, sample_pool_data):
        """Create sample state with pool and settings"""
        return {
            "pools": [sample_pool_data],
            "settings": {
                "threshold": 90,
                "balance_tolerance": 2
            }
        }
    
    @pytest.fixture
    def temp_state_file(self, sample_state):
        """Create a temporary state file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(sample_state, f)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        try:
            os.unlink(temp_file)
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_track_loads_pool_data_from_state(self, shadow_instance, mock_shadow_page, sample_state):
        """Test that track function loads pool data from JSON state"""
        pool_link = "https://www.shadow.so/liquidity/test-pool-1"
        
        with patch('utils.shadow_utils.load_state', return_value=sample_state):
            with patch.object(shadow_instance, 'get_pool_data_by_link', return_value=sample_state["pools"][0]) as mock_get_pool:
                with patch.object(shadow_instance, 'current_price_monitor', return_value=1.0):
                    with patch.object(shadow_instance, 'monitor', return_value=False):
                        with patch('asyncio.sleep', side_effect=KeyboardInterrupt):  # Break the loop
                            try:
                                await shadow_instance.track(None, mock_shadow_page, pool_link)
                            except KeyboardInterrupt:
                                pass
                
                # Verify pool data was requested
                mock_get_pool.assert_called_once_with(pool_link)
    
    @pytest.mark.asyncio
    async def test_track_loads_settings_from_state(self, shadow_instance, mock_shadow_page, sample_state):
        """Test that track function loads settings from JSON state"""
        pool_link = "https://www.shadow.so/liquidity/test-pool-1"
        
        with patch('utils.shadow_utils.load_state', return_value=sample_state) as mock_load:
            with patch.object(shadow_instance, 'get_pool_data_by_link', return_value=sample_state["pools"][0]):
                with patch.object(shadow_instance, 'current_price_monitor', return_value=1.0):
                    with patch.object(shadow_instance, 'monitor', return_value=False):
                        with patch('asyncio.sleep', side_effect=KeyboardInterrupt):
                            try:
                                await shadow_instance.track(None, mock_shadow_page, pool_link)
                            except KeyboardInterrupt:
                                pass
                
                # Verify state was loaded for settings
                mock_load.assert_called()
    
    @pytest.mark.asyncio
    async def test_track_handles_missing_pool_data(self, shadow_instance, mock_shadow_page, capsys):
        """Test track function handles missing pool data gracefully"""
        pool_link = "https://www.shadow.so/liquidity/nonexistent-pool"
        
        with patch.object(shadow_instance, 'get_pool_data_by_link', return_value=None):
            await shadow_instance.track(None, mock_shadow_page, pool_link)
            
            # Check that appropriate message was printed
            captured = capsys.readouterr()
            assert "Pool data not found for link" in captured.out
    
    @pytest.mark.asyncio
    async def test_track_navigates_to_manage_page(self, shadow_instance, mock_shadow_page, sample_state):
        """Test that track function navigates to the correct manage page"""
        pool_link = "https://www.shadow.so/liquidity/test-pool-1"
        expected_manage_url = "https://www.shadow.so/liquidity/manage/test-pool-1"
        
        with patch('utils.shadow_utils.load_state', return_value=sample_state):
            with patch.object(shadow_instance, 'get_pool_data_by_link', return_value=sample_state["pools"][0]):
                with patch.object(shadow_instance, 'current_price_monitor', return_value=1.0):
                    with patch.object(shadow_instance, 'monitor', return_value=False):
                        with patch('asyncio.sleep', side_effect=KeyboardInterrupt):
                            try:
                                await shadow_instance.track(None, mock_shadow_page, pool_link)
                            except KeyboardInterrupt:
                                pass
                
                # Verify navigation to manage page
                mock_shadow_page.goto.assert_called_with(expected_manage_url)
    
    @pytest.mark.asyncio
    async def test_track_token_switching_logic(self, shadow_instance, mock_shadow_page, sample_state):
        """Test track function handles token switching when needed"""
        pool_link = "https://www.shadow.so/liquidity/test-pool-1"
        
        # Mock different token in display vs pool data
        different_token_content = "SOL\u2002100\u2002USDC"
        mock_shadow_page.locator.return_value.text_content.return_value = different_token_content
        
        with patch('utils.shadow_utils.load_state', return_value=sample_state):
            with patch.object(shadow_instance, 'get_pool_data_by_link', return_value=sample_state["pools"][0]):
                with patch.object(shadow_instance, 'current_price_monitor', return_value=1.0):
                    with patch.object(shadow_instance, 'monitor', return_value=False):
                        with patch('asyncio.sleep', side_effect=KeyboardInterrupt):
                            try:
                                await shadow_instance.track(None, mock_shadow_page, pool_link)
                            except KeyboardInterrupt:
                                pass
                
                # Verify click was called for token switching
                mock_shadow_page.click.assert_called()
    
    @pytest.mark.asyncio
    async def test_track_monitoring_and_withdrawal_trigger(self, shadow_instance, mock_shadow_page, sample_state):
        """Test track function triggers withdrawal when monitor returns True"""
        pool_link = "https://www.shadow.so/liquidity/test-pool-1"
        
        with patch('utils.shadow_utils.load_state', return_value=sample_state):
            with patch.object(shadow_instance, 'get_pool_data_by_link', return_value=sample_state["pools"][0]):
                with patch.object(shadow_instance, 'current_price_monitor', return_value=1.4):  # Near threshold
                    with patch.object(shadow_instance, 'monitor', return_value=True):  # Trigger withdrawal
                        with patch.object(shadow_instance, 'withdraw') as mock_withdraw:
                            with patch.object(shadow_instance, 'rebalance') as mock_rebalance:
                                with patch.object(shadow_instance, 'add_pool_link') as mock_add_pool:
                                    with patch('asyncio.sleep', side_effect=KeyboardInterrupt):
                                        try:
                                            await shadow_instance.track(None, mock_shadow_page, pool_link)
                                        except KeyboardInterrupt:
                                            pass
                
                # Verify withdrawal was triggered
                mock_withdraw.assert_called_once_with(None, mock_shadow_page, pool_link)
    
    @pytest.mark.asyncio
    async def test_track_rebalancing_workflow(self, shadow_instance, mock_shadow_page, sample_state):
        """Test track function executes full rebalancing workflow"""
        pool_link = "https://www.shadow.so/liquidity/test-pool-1"
        
        # Mock available amount display
        mock_shadow_page.locator.return_value.nth.return_value.text_content.return_value = "Available: 75.25"
        
        with patch('utils.shadow_utils.load_state', return_value=sample_state):
            with patch.object(shadow_instance, 'get_pool_data_by_link', return_value=sample_state["pools"][0]):
                with patch.object(shadow_instance, 'current_price_monitor', return_value=1.4):
                    with patch.object(shadow_instance, 'monitor', return_value=True):
                        with patch.object(shadow_instance, 'withdraw') as mock_withdraw:
                            with patch.object(shadow_instance, 'rebalance') as mock_rebalance:
                                with patch.object(shadow_instance, 'add_pool_link') as mock_add_pool:
                                    with patch('asyncio.sleep', side_effect=KeyboardInterrupt):
                                        try:
                                            await shadow_instance.track(None, mock_shadow_page, pool_link)
                                        except KeyboardInterrupt:
                                            pass
                
                # Verify full workflow
                mock_withdraw.assert_called_once()
                mock_rebalance.assert_called_once()
                mock_add_pool.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_track_continuous_monitoring_loop(self, shadow_instance, mock_shadow_page, sample_state):
        """Test track function runs continuous monitoring loop with proper delays"""
        pool_link = "https://www.shadow.so/liquidity/test-pool-1"
        
        call_count = 0
        def side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count >= 3:  # Stop after 3 iterations
                raise KeyboardInterrupt
            return False
        
        with patch('utils.shadow_utils.load_state', return_value=sample_state):
            with patch.object(shadow_instance, 'get_pool_data_by_link', return_value=sample_state["pools"][0]):
                with patch.object(shadow_instance, 'current_price_monitor', return_value=1.0):
                    with patch.object(shadow_instance, 'monitor', side_effect=side_effect):
                        with patch('asyncio.sleep') as mock_sleep:
                            try:
                                await shadow_instance.track(None, mock_shadow_page, pool_link)
                            except KeyboardInterrupt:
                                pass
                
                # Verify multiple sleep calls (continuous monitoring)
                assert mock_sleep.call_count >= 2
                mock_sleep.assert_has_calls([call(5)] * mock_sleep.call_count)
    
    @pytest.mark.asyncio
    async def test_track_exits_when_no_browser_pages(self, shadow_instance, mock_shadow_page, sample_state):
        """Test track function exits when browser has no pages"""
        pool_link = "https://www.shadow.so/liquidity/test-pool-1"
        
        # Mock browser with no pages
        shadow_instance.browser.pages = []
        
        with patch('utils.shadow_utils.load_state', return_value=sample_state):
            with patch.object(shadow_instance, 'get_pool_data_by_link', return_value=sample_state["pools"][0]):
                with patch.object(shadow_instance, 'current_price_monitor') as mock_price_monitor:
                    # Function should exit immediately, so price monitor shouldn't be called
                    await shadow_instance.track(None, mock_shadow_page, pool_link)
                    
                    mock_price_monitor.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_track_uses_default_settings(self, shadow_instance, mock_shadow_page):
        """Test track function uses default settings when not present in state"""
        pool_link = "https://www.shadow.so/liquidity/test-pool-1"
        
        pool_data = {
            "link": pool_link,
            "range": "narrow",
            "token": "SOL",
            "amount": 50,
            "upper_range": 2.0,
            "lower_range": 1.0
        }
        
        state_without_settings = {
            "pools": [pool_data],
            "settings": {}  # Empty settings
        }
        
        with patch('utils.shadow_utils.load_state', return_value=state_without_settings):
            with patch.object(shadow_instance, 'get_pool_data_by_link', return_value=pool_data):
                with patch.object(shadow_instance, 'current_price_monitor', return_value=1.5):
                    with patch.object(shadow_instance, 'monitor') as mock_monitor:
                        with patch('asyncio.sleep', side_effect=KeyboardInterrupt):
                            try:
                                await shadow_instance.track(None, mock_shadow_page, pool_link)
                            except KeyboardInterrupt:
                                pass
                
                # Verify monitor was called with default threshold (90)
                mock_monitor.assert_called()
                args = mock_monitor.call_args[0]
                threshold = args[4]  # threshold is the 5th argument
                assert threshold == 90  # Default threshold


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

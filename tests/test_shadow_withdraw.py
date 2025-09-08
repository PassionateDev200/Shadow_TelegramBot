"""
Test file for the withdraw function from shadow_utils.py

This test file covers the withdraw functionality including:
- UI interaction simulation
- Pool removal from JSON state
- Error handling scenarios
"""

import pytest
import asyncio
import json
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
from utils.shadow_utils import Shadow
from models.pool import Pool
from utils.state import save_state, load_state


class TestWithdraw:
    """Test class for the withdraw function"""
    
    @pytest.fixture
    def mock_browser(self):
        """Create a mock browser for testing"""
        browser = MagicMock()
        return browser
    
    @pytest.fixture
    def shadow_instance(self, mock_browser):
        """Create a Shadow instance with mock browser"""
        return Shadow(mock_browser)
    
    @pytest.fixture
    def mock_withdraw_page(self):
        """Create a mock withdraw page with UI elements"""
        page = AsyncMock()
        page.get_by_role = MagicMock(return_value=AsyncMock())
        return page
    
    @pytest.fixture
    def sample_pools(self):
        """Create sample pools for testing"""
        return [
            Pool(
                link="https://www.shadow.so/liquidity/test-pool-1",
                range="wide",
                token="SHADOW",
                amount=100,
                upper_range=1.5,
                lower_range=0.5,
                owner_chat_id=12345,
                last_status="active"
            ),
            Pool(
                link="https://www.shadow.so/liquidity/test-pool-2", 
                range="narrow",
                token="SOL",
                amount=50,
                upper_range=2.0,
                lower_range=1.0,
                owner_chat_id=67890,
                last_status="active"
            )
        ]
    
    @pytest.fixture
    def temp_state_file(self, sample_pools):
        """Create a temporary state file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            state_data = {
                "pools": [
                    {
                        "link": pool.link,
                        "range": pool.range,
                        "token": pool.token,
                        "amount": pool.amount,
                        "upper_range": pool.upper_range,
                        "lower_range": pool.lower_range,
                        "owner_chat_id": pool.owner_chat_id,
                        "last_status": pool.last_status,
                        "meta": pool.meta
                    } for pool in sample_pools
                ],
                "settings": {
                    "threshold": 90,
                    "balance_tolerance": 2
                }
            }
            json.dump(state_data, f)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        try:
            os.unlink(temp_file)
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_withdraw_ui_interactions(self, shadow_instance, mock_withdraw_page):
        """Test that withdraw function performs correct UI interactions"""
        pool_link = "https://www.shadow.so/liquidity/test-pool-1"
        
        # Mock UI elements
        decrease_button = AsyncMock()
        percent_button = AsyncMock()
        withdraw_button = AsyncMock()
        
        mock_withdraw_page.get_by_role.side_effect = lambda role, name: {
            ("button", "Decrease Liquidity"): decrease_button,
            ("button", "100%"): percent_button,
            ("button", "Withdraw"): withdraw_button
        }.get((role, name), AsyncMock())
        
        with patch('utils.shadow_utils.load_state', return_value={"pools": [], "settings": {}}):
            with patch('utils.shadow_utils.save_state'):
                await shadow_instance.withdraw(None, mock_withdraw_page, pool_link)
        
        # Verify UI interactions
        decrease_button.click.assert_called_once()
        percent_button.click.assert_called_once()
        withdraw_button.click.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_withdraw_removes_pool_from_state(self, shadow_instance, mock_withdraw_page, temp_state_file):
        """Test that withdraw function removes the pool from JSON state"""
        pool_link = "https://www.shadow.so/liquidity/test-pool-1"
        
        # Mock UI elements
        mock_withdraw_page.get_by_role.return_value = AsyncMock()
        
        with patch('utils.shadow_utils.STATE_FILE', temp_state_file):
            await shadow_instance.withdraw(None, mock_withdraw_page, pool_link)
            
            # Load state and verify pool was removed
            state = load_state()
            remaining_pools = state.get("pools", [])
            
            # Should have 1 pool left (the other one)
            assert len(remaining_pools) == 1
            assert remaining_pools[0]["link"] == "https://www.shadow.so/liquidity/test-pool-2"
            assert pool_link not in [p["link"] for p in remaining_pools]
    
    @pytest.mark.asyncio
    async def test_withdraw_preserves_settings(self, shadow_instance, mock_withdraw_page, temp_state_file):
        """Test that withdraw function preserves settings when removing pool"""
        pool_link = "https://www.shadow.so/liquidity/test-pool-1"
        
        mock_withdraw_page.get_by_role.return_value = AsyncMock()
        
        with patch('utils.shadow_utils.STATE_FILE', temp_state_file):
            await shadow_instance.withdraw(None, mock_withdraw_page, pool_link)
            
            # Load state and verify settings are preserved
            state = load_state()
            settings = state.get("settings", {})
            
            assert settings["threshold"] == 90
            assert settings["balance_tolerance"] == 2
    
    @pytest.mark.asyncio
    async def test_withdraw_handles_nonexistent_pool(self, shadow_instance, mock_withdraw_page, temp_state_file):
        """Test withdraw function when pool doesn't exist in state"""
        nonexistent_pool = "https://www.shadow.so/liquidity/nonexistent-pool"
        
        mock_withdraw_page.get_by_role.return_value = AsyncMock()
        
        with patch('utils.shadow_utils.STATE_FILE', temp_state_file):
            # Should not raise exception
            await shadow_instance.withdraw(None, mock_withdraw_page, nonexistent_pool)
            
            # All original pools should still be there
            state = load_state()
            pools = state.get("pools", [])
            assert len(pools) == 2
    
    @pytest.mark.asyncio
    async def test_withdraw_handles_state_errors(self, shadow_instance, mock_withdraw_page, capsys):
        """Test withdraw function handles state loading/saving errors gracefully"""
        pool_link = "https://www.shadow.so/liquidity/test-pool-1"
        
        mock_withdraw_page.get_by_role.return_value = AsyncMock()
        
        with patch('utils.shadow_utils.load_state', side_effect=Exception("State load error")):
            # Should not raise exception
            await shadow_instance.withdraw(None, mock_withdraw_page, pool_link)
            
            # Check that error was printed
            captured = capsys.readouterr()
            assert "Error removing pool from state: State load error" in captured.out
    
    @pytest.mark.asyncio
    async def test_withdraw_empty_state(self, shadow_instance, mock_withdraw_page):
        """Test withdraw function with empty state"""
        pool_link = "https://www.shadow.so/liquidity/test-pool-1"
        
        mock_withdraw_page.get_by_role.return_value = AsyncMock()
        
        with patch('utils.shadow_utils.load_state', return_value={}):
            with patch('utils.shadow_utils.save_state') as mock_save:
                await shadow_instance.withdraw(None, mock_withdraw_page, pool_link)
                
                # Should still call save_state with empty pools
                mock_save.assert_called_once_with([], {})


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

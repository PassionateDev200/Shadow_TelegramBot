"""
Test file for the rebalance function from shadow_utils.py

This test file covers the rebalance functionality including:
- Navigation to trade page
- Token selection and input
- Swap execution
- Error handling scenarios
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from utils.shadow_utils import Shadow


class TestRebalance:
    """Test class for the rebalance function"""
    
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
    def mock_trade_page(self):
        """Create a mock trade page with UI elements"""
        page = AsyncMock()
        page.goto = AsyncMock()
        page.locator = MagicMock(return_value=AsyncMock())
        page.click = AsyncMock()
        page.fill = AsyncMock()
        page.get_by_role = MagicMock(return_value=AsyncMock())
        return page
    
    @pytest.mark.asyncio
    async def test_rebalance_navigates_to_trade_page(self, shadow_instance, mock_trade_page):
        """Test that rebalance function navigates to correct trade page"""
        tokens = ["SHADOW", "SOL"]
        amount = "100"
        
        # Mock locator elements
        locator_mock = AsyncMock()
        locator_mock.nth.return_value = AsyncMock()
        mock_trade_page.locator.return_value = locator_mock
        
        # Mock swap button
        swap_button = AsyncMock()
        swap_button.is_visible.return_value = True
        mock_trade_page.get_by_role.return_value = swap_button
        
        await shadow_instance.rebalance(mock_trade_page, tokens, amount)
        
        # Verify navigation
        mock_trade_page.goto.assert_called_once_with("https://www.shadow.so/trade")
    
    @pytest.mark.asyncio
    async def test_rebalance_handles_shadow_token_special_case(self, shadow_instance, mock_trade_page):
        """Test rebalance handles SHADOW token special case with icon click"""
        tokens = ["SHADOW", "S"]  # Special case where second token is "S"
        amount = "100"
        
        # Mock locator elements
        locator_mock = AsyncMock()
        locator_mock.nth.return_value = AsyncMock()
        mock_trade_page.locator.return_value = locator_mock
        
        # Mock swap button
        swap_button = AsyncMock()
        swap_button.is_visible.return_value = True
        mock_trade_page.get_by_role.return_value = swap_button
        
        await shadow_instance.rebalance(mock_trade_page, tokens, amount)
        
        # Verify special icon click for SHADOW token
        mock_trade_page.click.assert_any_call('[class="size-5 text-primary-light"]')
    
    @pytest.mark.asyncio
    async def test_rebalance_token_selection_and_input(self, shadow_instance, mock_trade_page):
        """Test that rebalance correctly selects tokens and fills amounts"""
        tokens = ["BTC", "ETH"]
        amount = "50.5"
        
        # Mock locator elements
        locator_mock = AsyncMock()
        locator_mock.nth.return_value = AsyncMock()
        mock_trade_page.locator.return_value = locator_mock
        
        # Mock swap button
        swap_button = AsyncMock()
        swap_button.is_visible.return_value = True
        mock_trade_page.get_by_role.return_value = swap_button
        
        await shadow_instance.rebalance(mock_trade_page, tokens, amount)
        
        # Verify token inputs
        expected_calls = [
            (('[class="form-control bg-dark py-2 pl-10 text-lg md:py-3 md:pl-14 md:text-2xl"]', "BTC")),
            (('[class="form-control bg-dark py-2 pl-10 text-lg md:py-3 md:pl-14 md:text-2xl"]', "ETH")),
            (('[class="w-full bg-transparent text-3xl font-bold outline-none placeholder:text-dark md:text-4xl text-light text-right"]', amount))
        ]
        
        for expected_call in expected_calls:
            mock_trade_page.fill.assert_any_call(*expected_call)
    
    @pytest.mark.asyncio
    async def test_rebalance_clicks_swap_when_visible(self, shadow_instance, mock_trade_page):
        """Test that rebalance clicks swap button when it's visible"""
        tokens = ["USDC", "SOL"]
        amount = "1000"
        
        # Mock locator elements
        locator_mock = AsyncMock()
        locator_mock.nth.return_value = AsyncMock()
        mock_trade_page.locator.return_value = locator_mock
        
        # Mock visible swap button
        swap_button = AsyncMock()
        swap_button.is_visible.return_value = True
        mock_trade_page.get_by_role.return_value = swap_button
        
        await shadow_instance.rebalance(mock_trade_page, tokens, amount)
        
        # Verify swap button interaction
        mock_trade_page.get_by_role.assert_called_with("button", name="Swap")
        swap_button.click.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rebalance_skips_swap_when_not_visible(self, shadow_instance, mock_trade_page):
        """Test that rebalance skips swap button when it's not visible"""
        tokens = ["USDC", "SOL"]
        amount = "1000"
        
        # Mock locator elements
        locator_mock = AsyncMock()
        locator_mock.nth.return_value = AsyncMock()
        mock_trade_page.locator.return_value = locator_mock
        
        # Mock invisible swap button
        swap_button = AsyncMock()
        swap_button.is_visible.return_value = False
        mock_trade_page.get_by_role.return_value = swap_button
        
        await shadow_instance.rebalance(mock_trade_page, tokens, amount)
        
        # Verify swap button was checked but not clicked
        swap_button.is_visible.assert_called_once()
        swap_button.click.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_rebalance_token_dropdown_selection(self, shadow_instance, mock_trade_page):
        """Test that rebalance clicks on token dropdown selections"""
        tokens = ["ORCA", "RAY"]
        amount = "25"
        
        # Mock locator elements
        dropdown_locator = AsyncMock()
        dropdown_locator.nth.return_value = AsyncMock()
        
        text_locator = AsyncMock()
        text_locator.nth.return_value = AsyncMock()
        
        def locator_side_effect(selector):
            if "flex items-center text-3xl font-medium" in selector:
                return text_locator
            elif "flex cursor-pointer hover:bg-dark" in selector:
                return dropdown_locator
            return AsyncMock()
        
        mock_trade_page.locator.side_effect = locator_side_effect
        
        # Mock swap button
        swap_button = AsyncMock()
        swap_button.is_visible.return_value = True
        mock_trade_page.get_by_role.return_value = swap_button
        
        await shadow_instance.rebalance(mock_trade_page, tokens, amount)
        
        # Verify dropdown clicks (should be called twice for each token)
        assert dropdown_locator.nth.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_rebalance_with_empty_tokens(self, shadow_instance, mock_trade_page):
        """Test rebalance handles empty token list gracefully"""
        tokens = []
        amount = "100"
        
        # Mock locator elements
        locator_mock = AsyncMock()
        locator_mock.nth.return_value = AsyncMock()
        mock_trade_page.locator.return_value = locator_mock
        
        # Mock swap button
        swap_button = AsyncMock()
        swap_button.is_visible.return_value = True
        mock_trade_page.get_by_role.return_value = swap_button
        
        # Should not raise exception
        await shadow_instance.rebalance(mock_trade_page, tokens, amount)
        
        # Still should navigate to trade page
        mock_trade_page.goto.assert_called_once_with("https://www.shadow.so/trade")
    
    @pytest.mark.asyncio
    async def test_rebalance_with_zero_amount(self, shadow_instance, mock_trade_page):
        """Test rebalance handles zero amount"""
        tokens = ["SOL", "USDC"]
        amount = "0"
        
        # Mock locator elements
        locator_mock = AsyncMock()
        locator_mock.nth.return_value = AsyncMock()
        mock_trade_page.locator.return_value = locator_mock
        
        # Mock swap button
        swap_button = AsyncMock()
        swap_button.is_visible.return_value = True
        mock_trade_page.get_by_role.return_value = swap_button
        
        await shadow_instance.rebalance(mock_trade_page, tokens, amount)
        
        # Should still fill the amount field with "0"
        mock_trade_page.fill.assert_any_call(
            '[class="w-full bg-transparent text-3xl font-bold outline-none placeholder:text-dark md:text-4xl text-light text-right"]',
            "0"
        )
    
    @pytest.mark.asyncio 
    async def test_rebalance_asyncio_sleep_timing(self, shadow_instance, mock_trade_page):
        """Test that rebalance includes proper timing delays"""
        tokens = ["SOL", "USDC"]
        amount = "100"
        
        # Mock locator elements
        locator_mock = AsyncMock()
        locator_mock.nth.return_value = AsyncMock()
        mock_trade_page.locator.return_value = locator_mock
        
        # Mock swap button
        swap_button = AsyncMock()
        swap_button.is_visible.return_value = True
        mock_trade_page.get_by_role.return_value = swap_button
        
        with patch('asyncio.sleep') as mock_sleep:
            await shadow_instance.rebalance(mock_trade_page, tokens, amount)
            
            # Verify sleep was called (for timing between operations)
            mock_sleep.assert_called_with(1)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

"""
Integration test for the /remove command with Shadow.so platform

This test demonstrates the complete workflow of the /remove command:
1. Validates pool link format
2. Connects to browser and MetaMask
3. Navigates to pool management page
4. Performs withdrawal steps
5. Handles MetaMask confirmation
6. Removes pool from monitoring state
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from bot.commands import Bot


class TestRemoveIntegration:
    """Integration test for /remove command"""
    
    @pytest.mark.asyncio
    async def test_complete_remove_workflow(self):
        """Test the complete /remove command workflow"""
        
        # Setup
        bot = Bot()
        bot.browser = MagicMock()
        
        # Mock update and context
        update = MagicMock()
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 12345
        update.effective_chat = MagicMock()
        update.effective_chat.id = 67890
        
        context = MagicMock()
        context.args = ["https://www.shadow.so/liquidity/manage/0x1234567890abcdef1234567890abcdef12345678/123"]
        
        # Mock the complete workflow
        with patch.object(bot, '_is_authorized', return_value=True):
            with patch.object(bot, '_has_stored_credentials', return_value=True):
                with patch.object(bot, '_load_stored_credentials'):
                    with patch('bot.commands.launch_browser', return_value=bot.browser):
                        with patch('bot.commands.metamask_connect', return_value=AsyncMock()):
                            with patch('bot.commands.shadow_connect', return_value=AsyncMock()):
                                with patch('bot.commands.save_state') as mock_save_state:
                                    with patch('bot.commands.load_state', return_value={"pools": [], "settings": {}}):
                                        
                                        # Mock the manage page and UI interactions
                                        mock_manage_page = AsyncMock()
                                        mock_manage_page.goto = AsyncMock()
                                        mock_manage_page.close = AsyncMock()
                                        
                                        # Mock UI buttons
                                        mock_decrease_button = AsyncMock()
                                        mock_percent_button = AsyncMock()
                                        mock_withdraw_button = AsyncMock()
                                        
                                        def mock_get_by_role(role, name):
                                            if name == "Decrease Liquidity":
                                                return mock_decrease_button
                                            elif name == "100%":
                                                return mock_percent_button
                                            elif name == "Withdraw":
                                                return mock_withdraw_button
                                            else:
                                                return AsyncMock()
                                        
                                        mock_manage_page.get_by_role = mock_get_by_role
                                        bot.browser.new_page = AsyncMock(return_value=mock_manage_page)
                                        
                                        # Mock MetaMask page
                                        mock_metamask_page = AsyncMock()
                                        mock_confirm_button = AsyncMock()
                                        mock_confirm_button.is_visible = AsyncMock(return_value=True)
                                        mock_metamask_page.get_by_role = MagicMock(return_value=mock_confirm_button)
                                        bot.browser.pages = [mock_metamask_page]
                                        
                                        # Execute the command
                                        await bot.remove_command(update, context)
                                        
                                        # Verify the complete workflow
                                        assert update.message.reply_text.call_count >= 6  # Multiple status messages
                                        
                                        # Check that all UI interactions were called
                                        mock_decrease_button.click.assert_called_once()
                                        mock_percent_button.click.assert_called_once()
                                        mock_withdraw_button.click.assert_called_once()
                                        mock_confirm_button.click.assert_called_once()
                                        
                                        # Check that state was saved
                                        mock_save_state.assert_called_once()
                                        
                                        # Check that page was closed
                                        mock_manage_page.close.assert_called_once()
                                        
                                        print("✅ Complete /remove workflow test passed!")


if __name__ == "__main__":
    # Run the integration test
    pytest.main([__file__, "-v", "-s"])


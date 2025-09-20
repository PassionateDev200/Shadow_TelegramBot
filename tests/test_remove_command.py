"""
Test file for the enhanced /remove command functionality

This test file covers the new /remove command that:
- Validates pool link format
- Checks wallet connection
- Performs actual withdrawal from Shadow.so
- Handles MetaMask transaction confirmation
- Removes pool from monitoring state
"""

import pytest
import asyncio
import json
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
from bot.commands import Bot
from models.pool import Pool
from utils.state import save_state, load_state


class TestRemoveCommand:
    """Test class for the enhanced /remove command"""
    
    @pytest.fixture
    def mock_browser(self):
        """Create a mock browser for testing"""
        browser = MagicMock()
        return browser
    
    @pytest.fixture
    def bot_instance(self, mock_browser):
        """Create a Bot instance with mock browser"""
        bot = Bot()
        bot.browser = mock_browser
        return bot
    
    @pytest.fixture
    def mock_update(self):
        """Create a mock Telegram update"""
        update = MagicMock()
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 12345
        update.effective_chat = MagicMock()
        update.effective_chat.id = 67890
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock Telegram context"""
        context = MagicMock()
        context.args = []
        return context
    
    @pytest.fixture
    def sample_pools(self):
        """Create sample pools for testing"""
        return [
            Pool(
                link="https://www.shadow.so/liquidity/manage/0x1234567890abcdef1234567890abcdef12345678/123",
                range="wide",
                token="SHADOW",
                amount=100,
                upper_range=1.5,
                lower_range=0.5,
                owner_chat_id=12345,
                last_status="active"
            ),
            Pool(
                link="https://www.shadow.so/liquidity/manage/0xabcdef1234567890abcdef1234567890abcdef12/456", 
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
    async def test_remove_command_unauthorized(self, bot_instance, mock_update, mock_context):
        """Test that unauthorized users are rejected"""
        # Mock unauthorized user
        with patch.object(bot_instance, '_is_authorized', return_value=False):
            await bot_instance.remove_command(mock_update, mock_context)
            mock_update.message.reply_text.assert_called_with("Unauthorized.")
    
    @pytest.mark.asyncio
    async def test_remove_command_no_args(self, bot_instance, mock_update, mock_context):
        """Test that missing arguments are handled"""
        with patch.object(bot_instance, '_is_authorized', return_value=True):
            await bot_instance.remove_command(mock_update, mock_context)
            expected_message = "Usage: /remove [pool link]\nExample: /remove https://www.shadow.so/liquidity/manage/0x1234.../123"
            mock_update.message.reply_text.assert_called_with(expected_message)
    
    @pytest.mark.asyncio
    async def test_remove_command_invalid_link_format(self, bot_instance, mock_update, mock_context):
        """Test that invalid pool link formats are rejected"""
        mock_context.args = ["https://invalid-link.com/pool/123"]
        
        with patch.object(bot_instance, '_is_authorized', return_value=True):
            await bot_instance.remove_command(mock_update, mock_context)
            expected_message = "❌ Invalid pool link format. Expected: https://www.shadow.so/liquidity/manage/[Contract address]/[Pool ID]"
            mock_update.message.reply_text.assert_called_with(expected_message)
    
    @pytest.mark.asyncio
    async def test_remove_command_no_credentials(self, bot_instance, mock_update, mock_context):
        """Test that missing MetaMask credentials are handled"""
        mock_context.args = ["https://www.shadow.so/liquidity/manage/0x1234567890abcdef1234567890abcdef12345678/123"]
        
        with patch.object(bot_instance, '_is_authorized', return_value=True):
            with patch.object(bot_instance, '_has_stored_credentials', return_value=False):
                await bot_instance.remove_command(mock_update, mock_context)
                expected_message = "❌ MetaMask credentials not found. Please use /connect first with your password and 12-word seed phrase.\nUsage: /connect [password] [word1] [word2] ... [word12]"
                mock_update.message.reply_text.assert_called_with(expected_message)
    
    @pytest.mark.asyncio
    async def test_remove_command_successful_withdrawal(self, bot_instance, mock_update, mock_context, temp_state_file):
        """Test successful withdrawal process"""
        pool_link = "https://www.shadow.so/liquidity/manage/0x1234567890abcdef1234567890abcdef12345678/123"
        mock_context.args = [pool_link]
        
        # Mock successful withdrawal process
        mock_manage_page = AsyncMock()
        mock_manage_page.get_by_role = MagicMock(return_value=AsyncMock())
        mock_manage_page.goto = AsyncMock()
        mock_manage_page.close = AsyncMock()
        
        # Mock browser operations
        bot_instance.browser.new_page = AsyncMock(return_value=mock_manage_page)
        
        with patch.object(bot_instance, '_is_authorized', return_value=True):
            with patch.object(bot_instance, '_has_stored_credentials', return_value=True):
                with patch.object(bot_instance, '_load_stored_credentials'):
                    with patch('bot.commands.launch_browser', return_value=bot_instance.browser):
                        with patch('bot.commands.metamask_connect', return_value=AsyncMock()):
                            with patch('bot.commands.shadow_connect', return_value=AsyncMock()):
                                with patch('bot.commands.save_state') as mock_save_state:
                                    with patch('bot.commands.load_state') as mock_load_state:
                                        # Mock state loading
                                        mock_load_state.return_value = {
                                            "pools": [
                                                {
                                                    "link": pool_link,
                                                    "range": "wide",
                                                    "token": "SHADOW",
                                                    "amount": 100,
                                                    "upper_range": 1.5,
                                                    "lower_range": 0.5,
                                                    "owner_chat_id": 12345,
                                                    "last_status": "active",
                                                    "meta": {}
                                                }
                                            ],
                                            "settings": {"threshold": 90, "balance_tolerance": 2}
                                        }
                                        
                                        await bot_instance.remove_command(mock_update, mock_context)
                                        
                                        # Verify the process
                                        mock_update.message.reply_text.assert_any_call("🔄 Starting withdrawal process...")
                                        mock_update.message.reply_text.assert_any_call("🌐 Navigating to pool management page...")
                                        mock_update.message.reply_text.assert_any_call("📉 Clicking 'Decrease Liquidity' button...")
                                        mock_update.message.reply_text.assert_any_call("💯 Selecting '100%' withdrawal...")
                                        mock_update.message.reply_text.assert_any_call("💰 Clicking 'Withdraw' button...")
                                        mock_update.message.reply_text.assert_any_call("🔐 Confirming transaction in MetaMask...")
                                        
                                        # Verify pool was removed from state
                                        mock_save_state.assert_called_once()
                                        mock_manage_page.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_command_wallet_connection_handling(self, bot_instance, mock_update, mock_context):
        """Test wallet connection handling during withdrawal"""
        pool_link = "https://www.shadow.so/liquidity/manage/0x1234567890abcdef1234567890abcdef12345678/123"
        mock_context.args = [pool_link]
        
        # Mock manage page with connect wallet button
        mock_manage_page = AsyncMock()
        mock_connect_button = AsyncMock()
        mock_connect_button.is_visible = AsyncMock(return_value=True)
        mock_manage_page.get_by_role = MagicMock(return_value=mock_connect_button)
        mock_manage_page.goto = AsyncMock()
        mock_manage_page.close = AsyncMock()
        
        # Mock browser with MetaMask page
        mock_metamask_page = AsyncMock()
        mock_metamask_page.get_by_role = MagicMock(return_value=AsyncMock())
        bot_instance.browser.pages = [mock_metamask_page]
        bot_instance.browser.new_page = AsyncMock(return_value=mock_manage_page)
        
        with patch.object(bot_instance, '_is_authorized', return_value=True):
            with patch.object(bot_instance, '_has_stored_credentials', return_value=True):
                with patch.object(bot_instance, '_load_stored_credentials'):
                    with patch('bot.commands.launch_browser', return_value=bot_instance.browser):
                        with patch('bot.commands.metamask_connect', return_value=AsyncMock()):
                            with patch('bot.commands.shadow_connect', return_value=AsyncMock()):
                                with patch('bot.commands.save_state'):
                                    with patch('bot.commands.load_state', return_value={"pools": [], "settings": {}}):
                                        await bot_instance.remove_command(mock_update, mock_context)
                                        
                                        # Verify wallet connection was attempted
                                        mock_connect_button.click.assert_called_once()
                                        mock_update.message.reply_text.assert_any_call("🔗 Wallet not connected, connecting...")
    
    @pytest.mark.asyncio
    async def test_remove_command_error_handling(self, bot_instance, mock_update, mock_context):
        """Test error handling during withdrawal process"""
        pool_link = "https://www.shadow.so/liquidity/manage/0x1234567890abcdef1234567890abcdef12345678/123"
        mock_context.args = [pool_link]
        
        # Mock browser that raises an exception
        bot_instance.browser = None
        
        with patch.object(bot_instance, '_is_authorized', return_value=True):
            with patch.object(bot_instance, '_has_stored_credentials', return_value=True):
                with patch.object(bot_instance, '_load_stored_credentials'):
                    with patch('bot.commands.launch_browser', side_effect=Exception("Browser launch failed")):
                        with patch('bot.commands.notify_admins', return_value=AsyncMock()) as mock_notify:
                            await bot_instance.remove_command(mock_update, mock_context)
                            
                            # Verify error handling
                            mock_update.message.reply_text.assert_any_call("🔄 Starting withdrawal process...")
                            mock_update.message.reply_text.assert_any_call("🔌 Connecting to browser...")
                            mock_update.message.reply_text.assert_any_call("❌ Withdrawal failed: Browser launch failed...")
                            mock_notify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_command_ui_interaction_failures(self, bot_instance, mock_update, mock_context):
        """Test handling of UI interaction failures"""
        pool_link = "https://www.shadow.so/liquidity/manage/0x1234567890abcdef1234567890abcdef12345678/123"
        mock_context.args = [pool_link]
        
        # Mock manage page with failing UI interactions
        mock_manage_page = AsyncMock()
        mock_manage_page.goto = AsyncMock()
        mock_manage_page.close = AsyncMock()
        
        # Mock get_by_role to raise exception for Decrease Liquidity button
        def mock_get_by_role(role, name):
            if name == "Decrease Liquidity":
                raise Exception("Button not found")
            return AsyncMock()
        
        mock_manage_page.get_by_role = mock_get_by_role
        bot_instance.browser = MagicMock()
        bot_instance.browser.new_page = AsyncMock(return_value=mock_manage_page)
        
        with patch.object(bot_instance, '_is_authorized', return_value=True):
            with patch.object(bot_instance, '_has_stored_credentials', return_value=True):
                with patch.object(bot_instance, '_load_stored_credentials'):
                    await bot_instance.remove_command(mock_update, mock_context)
                    
                    # Verify error handling
                    mock_update.message.reply_text.assert_any_call("❌ Failed to click 'Decrease Liquidity' button: Button not found")
                    mock_manage_page.close.assert_called_once()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])


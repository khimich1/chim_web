# LINE Integration

> Messaging for Japan market (97M+ users, 94% reach)

## Overview

Official LINE MCP server for sending messages via LINE Official Account. Essential for Japan, Taiwan, Thailand, and Indonesia markets.

## Market Reach

| Country | Users | Penetration |
|---------|-------|-------------|
| Japan | 97M+ | 94% |
| Taiwan | 21M+ | 90% |
| Thailand | 53M+ | 75% |
| Indonesia | 90M+ | 33% |

## Capabilities

| Tool | Description |
|------|-------------|
| `push_text_message` | Send text message to user |
| `push_flex_message` | Send rich flex message |
| `broadcast_message` | Broadcast to all followers |
| `get_profile` | Get user profile info |

## Authentication

```bash
export LINE_CHANNEL_ACCESS_TOKEN="xxx"
export LINE_CHANNEL_SECRET="xxx"
export LINE_DESTINATION_USER_ID="Uxxxxx"
```

### Setup
1. Create LINE Official Account at [manager.line.biz](https://manager.line.biz)
2. Enable Messaging API
3. Get Channel Access Token from LINE Developers Console

## Use Cases

### 1. Customer Notification
```
Send order confirmation
→ push_text_message(user_id="Uxxx", text="ご注文ありがとうございます！")
```

### 2. Rich Promotion
```
Send promotional flex message
→ push_flex_message(user_id="Uxxx", flex_content={...promotion_layout})
```

### 3. Broadcast Campaign
```
Announce sale to all followers
→ broadcast_message(message="🎉 本日限定セール！最大50%オフ")
```

## Integration with Marketing

- `/sequence:welcome` → LINE welcome sequence
- `/campaign:plan` → Japan market campaigns
- `/crm:segment` → Segment LINE users

## Note

LINE is the #1 messaging app in Japan. For Japan market, LINE marketing is essential - more effective than email for consumer reach.

## Related
- [Zalo](../zalo/) - Vietnam market equivalent
- [Slack](../slack/) - Internal team messaging

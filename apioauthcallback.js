export default function handler(req, res) {
    // 设置CORS头
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        res.status(200).end();
        return;
    }

    const { code, state, error, error_description } = req.query;

    if (error) {
        res.status(400).json({
            success: false,
            error: error,
            error_description: error_description
        });
        return;
    }

    if (code) {
        res.status(200).json({
            success: true,
            code: code,
            state: state,
            message: 'Authorization code received successfully'
        });
        return;
    }

    res.status(400).json({
        success: false,
        error: 'invalid_request',
        error_description: 'No authorization code or error received'
    });
}
```

#### 3. 创建 `vercel.json`

```json
{
  "rewrites": [
    {
      "source": "/oauth/callback",
      "destination": "/index.html"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        }
      ]
    }
  ]
}
import { NextResponse } from 'next/server';

interface LoginRequest {
  username: string;
  password: string;
}

// Mock user database
const MOCK_USERS = [
  {
    id: '1',
    username: 'admin',
    password: 'admin123',
    roles: ['ADMIN'],
  },
  {
    id: '2',
    username: 'analyst',
    password: 'analyst123',
    roles: ['ANALYST'],
  },
  {
    id: '3',
    username: 'auditor',
    password: 'auditor123',
    roles: ['AUDITOR'],
  },
  {
    id: '4',
    username: 'monitor',
    password: 'monitor123',
    roles: ['MONITOR'],
  },
];

export async function POST(request: Request) {
  try {
    const body: LoginRequest = await request.json();
    const { username, password } = body;

    // Find user in mock database
    const user = MOCK_USERS.find(
      (u) => u.username === username && u.password === password
    );

    if (user) {
      // Generate a mock JWT token (in production, use real JWT)
      const token = `mock-jwt-token-${user.id}-${Date.now()}`;

      return NextResponse.json({
        token,
        user: {
          userId: user.id,
          username: user.username,
          roles: user.roles,
        },
      });
    }

    // Invalid credentials
    return NextResponse.json(
      { message: '用户名或密码错误' },
      { status: 401 }
    );
  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json(
      { message: '服务器错误，请稍后重试' },
      { status: 500 }
    );
  }
}

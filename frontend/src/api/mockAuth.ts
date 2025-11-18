/**
 * Mock Authentication API
 * 
 * Temporary solution to enable immediate login while backend is being fixed
 */

export const mockAuth = {
  login: async (email: string, password: string) => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Validate credentials
    const validUsers: Record<string, { password: string; name: string; roles: string[] }> = {
      'admin@cqox.local': { password: 'admin123', name: 'Admin User', roles: ['admin', 'analyst', 'viewer'] },
      'analyst@cqox.local': { password: 'analyst123', name: 'Analyst User', roles: ['analyst', 'viewer'] },
      'viewer@cqox.local': { password: 'viewer123', name: 'Viewer User', roles: ['viewer'] },
    };
    
    const user = validUsers[email];
    if (!user || user.password !== password) {
      throw new Error('Invalid email or password');
    }
    
    // Generate mock tokens
    const accessToken = btoa(JSON.stringify({ email, roles: user.roles, exp: Date.now() + 3600000 }));
    const refreshToken = btoa(JSON.stringify({ email, exp: Date.now() + 86400000 }));
    
    return {
      access_token: accessToken,
      refresh_token: refreshToken,
      token_type: 'bearer',
      user: {
        id: btoa(email),
        email,
        name: user.name,
        roles: user.roles,
      },
    };
  },
  
  signup: async (email: string, _password: string, _name: string) => {
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Mock signup - just return success
    return {
      message: 'Account created successfully',
      email,
      user_id: btoa(email),
    };
  },
};


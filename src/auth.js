export const roles = ['admin', 'agronomist', 'billing'];

export const permissions = {
  field: {
    read: ['admin', 'agronomist', 'billing'],
    update: ['admin', 'agronomist'],
  },
  invoice: {
    read: ['admin', 'billing', 'agronomist'],
    update: ['admin', 'billing'],
  },
  event: {
    read: ['admin', 'agronomist', 'billing'],
    create: ['admin', 'agronomist'],
  },
};

export function attachUser(req, _res, next) {
  const userId = req.header('x-user-id') || 'demo-user';
  const role = req.header('x-user-role');
  if (!role || !roles.includes(role)) {
    req.user = { id: userId, role: 'agronomist' };
  } else {
    req.user = { id: userId, role };
  }
  next();
}

export function authorize(resource, action) {
  return (req, res, next) => {
    const allowedRoles = permissions[resource]?.[action] || [];
    if (!allowedRoles.includes(req.user.role)) {
      return res.status(403).json({
        error: 'forbidden',
        message: `Role ${req.user.role} cannot ${action} ${resource}s`,
      });
    }
    next();
  };
}

export function hasPermission(role, resource, action) {
  const allowedRoles = permissions[resource]?.[action] || [];
  return allowedRoles.includes(role);
}

import jwt from 'jsonwebtoken';
import dotenv from 'dotenv';
dotenv.config();

const secret = process.env.JWT_SECRET || 'athena-secret-key';
const token = jwt.sign({ sub: 'student-uuid-123' }, secret, { expiresIn: '1h' });

console.log('Use este token no Header Authorization:');
console.log(`Bearer ${token}`);

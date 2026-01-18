module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  moduleFileExtensions: ['ts', 'js', 'json', 'node'],
  roots: ['<rootDir>/src'],
  testRegex: '(/__tests__/.*|(\.|/)(test|spec))\.(ts|js)?$',
  setupFiles: ['<rootDir>/src/setupTests.ts'],
  transform: {
    '^.+\.(ts|tsx)$': 'ts-jest',
  },
  moduleNameMapper: {
    '^@src/(.*)$': '<rootDir>/src/$1',
  },
};


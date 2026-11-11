const express = require('express');
const router = express.Router();

function requireRole(role) {
  return (req, res, next) => (req.user && req.user.role === role ? next() : res.sendStatus(403));
}

router.get('/', (req, res) => res.json([]));
router.post('/:id/archive', requireRole('editor'), (req, res) => res.sendStatus(204));

module.exports = router;

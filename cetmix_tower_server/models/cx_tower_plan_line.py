# Copyright (C) 2022 Cetmix OÜ
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class CxTowerPlanLine(models.Model):
    _name = "cx.tower.plan.line"
    _order = "sequence, plan_id"
    _description = "Cetmix Tower Flight Plan Line"

    active = fields.Boolean(related="plan_id.active", readonly=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(related="command_id.name", readonly=True)
    plan_id = fields.Many2one(
        string="Flight Plan", comodel_name="cx.tower.plan", auto_join=True
    )
    command_id = fields.Many2one(comodel_name="cx.tower.command", required=True)
    path = fields.Char(
        help="Location where command will be executed. Overrides command default path. "
        "You can use {{ variables }} in path",
    )

    use_sudo = fields.Boolean(
        help="Will use sudo based on server settings."
        "If no sudo is configured will run without sudo"
    )
    action_ids = fields.One2many(
        string="Actions",
        comodel_name="cx.tower.plan.line.action",
        inverse_name="line_id",
        auto_join=True,
        help="Actions trigger based on command result."
        " If empty next command will be executed",
    )
    command_code = fields.Text(related="command_id.code", readonly=True)

    access_level = fields.Selection(
        related="plan_id.access_level",
        readonly=True,
        store=True,
    )

    def _execute(self, server, plan_log_record, **kwargs):
        """Execute command from the Flight Plan line

        Args:
            server (cx.tower.server()): Server object
            plan_log_record (cx.tower.plan.log()): Log record object
            kwargs (dict): Optional arguments
                Following are supported but not limited to:
                    - "plan_log": {values passed to flightplan logger}
                    - "log": {values passed to command logger}
                    - "key": {values passed to key parser}

        """
        self.ensure_one()

        # Set current line as currently executed in log
        plan_log_record.plan_line_executed_id = self

        # Pass plan_log to command so it will be saved in command log
        log_vals = kwargs.get("log", {})
        log_vals.update({"plan_log_id": plan_log_record.id})
        kwargs.update({"log": log_vals})

        # Set 'sudo' value
        use_sudo = self.use_sudo and server.use_sudo
        # Use sudo to bypass access rules for execute command with higher access level
        command_id = self.sudo().command_id

        # Set path
        path = self.path or self.command_id.path

        server.execute_command(command_id, path, sudo=use_sudo, **kwargs)

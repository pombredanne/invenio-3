# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from invenio.legacy.dbquery import run_sql

depends_on = ['invenio_release_1_1_0']

def info():
    return "New selfcite tables"

def do_upgrade():
    run_sql("""
    CREATE TABLE IF NOT EXISTS `rnkRECORDSCACHE` (
      `id_bibrec` int(10) unsigned NOT NULL,
      `authorid` bigint(10) NOT NULL,
      PRIMARY KEY (`id_bibrec`,`authorid`)
    ) ENGINE=MyISAM""")

    run_sql("""
    CREATE TABLE IF NOT EXISTS `rnkEXTENDEDAUTHORS` (
      `id` int(10) unsigned NOT NULL,
      `authorid` bigint(10) NOT NULL,
      PRIMARY KEY (`id`,`authorid`)
    ) ENGINE=MyISAM""")

    run_sql("""
    CREATE TABLE IF NOT EXISTS `rnkSELFCITES` (
      `id_bibrec` int(10) unsigned NOT NULL,
      `count` int(10) unsigned NOT NULL,
      `references` text NOT NULL,
      `last_updated` datetime NOT NULL,
      PRIMARY KEY (`id_bibrec`)
    ) ENGINE=MyISAM""")

def estimate():
    return 1

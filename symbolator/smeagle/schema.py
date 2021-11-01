# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

# Fields schema

fields = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["name"],
        # We allow additional properties here, because we can have additional underlying types
        "additionalProperties": True,
        "properties": {
            "name": {"type": "string"},
            "class": {"type": "string"},
            "type": {"type": "string"},
            "size": {"type": ["string", "number"]},
            # TODO should we add validation of when fields is allowed?
            # This indicates that fields can be recursive
            "fields": {"$ref": "#"},
        },
    },
}

# Underlying type schema
underlying_type = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string"},
        "class": {"type": "string"},
        "type": {"type": "string"},
        "size": {"type": ["string", "number"]},
        "fields": fields,
    },
}


# Schema for smeagle model
model_schema = {
    "$schema": "http://json-schema.org/schema#",
    "title": "build-abi-containers package schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["library", "locations"],
    "properties": {
        "library": {"type": "string"},
        "locations": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["function"],
                "properties": {
                    "function": {
                        "type": "object",
                        "required": ["name"],
                        "properties": {
                            "name": {"type": "string"},
                            "parameters": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "name": {"type": "string"},
                                        "indirections": {"type": ["string", "null"]},
                                        "class": {"type": "string"},
                                        "type": {"type": "string"},
                                        "size": {"type": ["string", "number"]},
                                        "location": {"type": "string"},
                                        "fields": fields,
                                        "underlying_type": underlying_type,
                                        "direction": {
                                            "type": ["string", "number"],
                                            "enum": ["import", "export", "unknown"],
                                        },
                                    },
                                },
                            },
                        },
                    }
                },
            },
        },
    },
}

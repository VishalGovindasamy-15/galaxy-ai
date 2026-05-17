"""Contract builder — Domain agents use this to create execution contracts.

Provides a fluent API for building structured contracts from domain
task specifications. Validates contracts before they're sent to workers.
"""

from __future__ import annotations

import logging
from typing import Any

from galaxy.contracts.types import (
    ChunkOperation,
    ConstraintLevel,
    ContractStatus,
    ExecutionContract,
    ParameterSpec,
    ReturnSpec,
)

logger = logging.getLogger(__name__)


class ContractValidationError(Exception):
    """Raised when a contract fails validation."""
    pass


class ContractBuilder:
    """Fluent builder for creating ExecutionContracts.

    Usage:
        contract = (
            ContractBuilder("backend")
            .target("auth/service.py", "create_jwt_token")
            .operation(ChunkOperation.CREATE_FUNCTION)
            .description("Create a JWT token for authenticated users")
            .param("user_id", "int", description="User's database ID")
            .param("secret", "str", description="JWT signing secret")
            .returns("str", "Encoded JWT token string")
            .depends_on("jwt", "datetime")
            .constraint("security", "high")
            .validate_with("returns valid JWT", "expires in 1h")
            .build()
        )
    """

    def __init__(self, domain: str = "") -> None:
        self._domain = domain
        self._target_file = ""
        self._function_name = ""
        self._operation = ChunkOperation.CREATE_FUNCTION
        self._description = ""
        self._parameters: list[ParameterSpec] = []
        self._return_spec = ReturnSpec()
        self._dependencies: list[str] = []
        self._constraints: dict[str, str] = {}
        self._validation: list[str] = []
        self._context = ""

    def target(self, file_path: str, function_name: str = "") -> ContractBuilder:
        """Set the target file and function name."""
        self._target_file = file_path
        self._function_name = function_name
        return self

    def operation(self, op: ChunkOperation) -> ContractBuilder:
        """Set the chunk operation type."""
        self._operation = op
        return self

    def description(self, desc: str) -> ContractBuilder:
        """Set the description of what this code should do."""
        self._description = desc
        return self

    def param(
        self,
        name: str,
        type_hint: str = "Any",
        default: str | None = None,
        description: str = "",
    ) -> ContractBuilder:
        """Add a parameter specification."""
        self._parameters.append(ParameterSpec(
            name=name,
            type_hint=type_hint,
            default=default,
            description=description,
        ))
        return self

    def returns(self, type_hint: str = "None", description: str = "") -> ContractBuilder:
        """Set the return type specification."""
        self._return_spec = ReturnSpec(type_hint=type_hint, description=description)
        return self

    def depends_on(self, *deps: str) -> ContractBuilder:
        """Add import dependencies."""
        self._dependencies.extend(deps)
        return self

    def constraint(self, key: str, value: str) -> ContractBuilder:
        """Add a constraint."""
        self._constraints[key] = value
        return self

    def validate_with(self, *expectations: str) -> ContractBuilder:
        """Add expected behaviors/validations."""
        self._validation.extend(expectations)
        return self

    def context(self, ctx: str) -> ContractBuilder:
        """Add additional context for the worker."""
        self._context = ctx
        return self

    def build(self, validate: bool = True) -> ExecutionContract:
        """Build the execution contract.

        Args:
            validate: Whether to validate the contract before returning.

        Returns:
            The built ExecutionContract.

        Raises:
            ContractValidationError: If validation fails.
        """
        contract = ExecutionContract(
            domain=self._domain,
            target_file=self._target_file,
            function_name=self._function_name,
            operation=self._operation,
            description=self._description,
            parameters=self._parameters.copy(),
            return_spec=self._return_spec,
            dependencies=self._dependencies.copy(),
            constraints=self._constraints.copy(),
            validation=self._validation.copy(),
            context=self._context,
            status=ContractStatus.READY,
        )

        if validate:
            self._validate(contract)

        logger.debug(
            "Built contract: %s → %s (%s)",
            contract.target_file,
            contract.function_name,
            contract.operation.value,
        )
        return contract

    def _validate(self, contract: ExecutionContract) -> None:
        """Validate a contract has required fields."""
        errors: list[str] = []

        if not contract.target_file:
            errors.append("target_file is required")

        if not contract.function_name and contract.operation not in (
            ChunkOperation.CREATE_FILE,
            ChunkOperation.ADD_IMPORT,
            ChunkOperation.APPEND_CODE,
        ):
            errors.append("function_name is required for this operation")

        if not contract.description:
            errors.append("description is required")

        if errors:
            raise ContractValidationError(
                f"Contract validation failed: {'; '.join(errors)}"
            )

    def reset(self) -> ContractBuilder:
        """Reset builder for reuse with same domain."""
        self._target_file = ""
        self._function_name = ""
        self._operation = ChunkOperation.CREATE_FUNCTION
        self._description = ""
        self._parameters = []
        self._return_spec = ReturnSpec()
        self._dependencies = []
        self._constraints = {}
        self._validation = []
        self._context = ""
        return self


def build_contract_from_dict(data: dict[str, Any]) -> ExecutionContract:
    """Build a contract from a dictionary (e.g., LLM output).

    This is the primary way Domain agents will create contracts —
    the LLM outputs a structured dict, which we convert to a contract.
    """
    builder = ContractBuilder(data.get("domain", ""))
    builder.target(
        data.get("target_file", ""),
        data.get("function_name", data.get("function", "")),
    )

    if "operation" in data:
        try:
            builder.operation(ChunkOperation(data["operation"]))
        except ValueError:
            builder.operation(ChunkOperation.CREATE_FUNCTION)

    if "description" in data:
        builder.description(data["description"])

    for param in data.get("parameters", []):
        if isinstance(param, dict):
            builder.param(
                name=param.get("name", ""),
                type_hint=param.get("type", param.get("type_hint", "Any")),
                default=param.get("default"),
                description=param.get("description", ""),
            )

    if "return_type" in data or "returns" in data or "return_spec" in data:
        ret = data.get("return_spec", data.get("returns", {}))
        if isinstance(ret, dict):
            builder.returns(
                ret.get("type_hint", ret.get("type", "None")),
                ret.get("description", ""),
            )
        elif isinstance(ret, str):
            builder.returns(ret)

    for dep in data.get("dependencies", []):
        builder.depends_on(dep)

    for key, value in data.get("constraints", {}).items():
        builder.constraint(key, value)

    for v in data.get("validation", []):
        builder.validate_with(v)

    if "context" in data:
        builder.context(data["context"])

    return builder.build(validate=False)

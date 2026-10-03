import logging,sys,structlog
def configure_logging(level="INFO"):
    n=getattr(logging,level.upper(),logging.INFO);logging.basicConfig(stream=sys.stdout,level=n,format="%(message)s",force=True);structlog.configure(processors=[structlog.contextvars.merge_contextvars,structlog.processors.TimeStamper(fmt="iso",utc=True),structlog.processors.add_log_level,structlog.processors.JSONRenderer()],wrapper_class=structlog.make_filtering_bound_logger(n),logger_factory=structlog.PrintLoggerFactory(),cache_logger_on_first_use=True)

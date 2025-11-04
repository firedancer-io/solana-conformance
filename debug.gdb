set follow-fork-mode child
set detach-on-fork off
set schedule-multiple on

# Can set breakpoints after these with autocomplete
# Or simply `continue`

catch load libfd_exec_sol_compat.so
commands 1
delete 1
end

catch load libsolfuzz_agave.so
commands 2
delete 2
end

define killi
    if $_inferior == 1
        echo killi: already on inferior 1; nothing to kill.\n
        return
    end

    kill
    inferior 1
end

document killi
Kill the current inferior (unless it is #1) and then select inferior 1.
end

alias ki = killi

run
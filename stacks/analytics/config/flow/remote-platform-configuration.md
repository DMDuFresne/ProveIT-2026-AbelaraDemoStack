# Remote Platform Configuration

> Source: [Flow Support - Remote Platform Configuration](https://support.flow-software.com/hc/en-us/articles/14159155706898-Remote-Platform-Configuration)

## When Would I Need to Configure a Remote Platform?

If a node hosting a Flow Platform cannot access the Flow instance's SQL database, then a Remote Platform is required.

In normal operation, the Flow Bootstrap service needs to communicate with the SQL server where the Flow instance resides, either via Windows or SQL authentication.

But if we start looking at IIoT and cloud offerings, the remote Bootstrap service might not be able to communicate directly with SQL. Likewise with applications spanning multiple domains and workgroups.

In these cases, a remote platform can be configured to communicate through another platform. All that is required is an outgoing connection to the remote platform and communication must be allowed through the Platform communication port, which is port **4501** by default.

## How Do I Configure a Remote Platform?

There are 2 steps that need to be completed to configure a Remote Platform:

1. Configuration of the Platform in the Flow Configuration tool
2. Configuration of the `Platforms.settings` file on the Remote Platform

---

## Step 1: Configuration in the Flow Config Tool

To create a remote platform, one would create a platform as normal in the deployment view. Rename the Platform to describe that this would be a remote platform.

A Remote Platform must be associated with a main platform that it needs to communicate back to. This can be done by dragging the Remote Platform onto its main platform in the deployment view.

---

## Step 2: Configuration of the Platforms.settings File

The Bootstrap Service on the Remote Platform must be configured to start up as a remote platform and it needs to know the endpoint of its main platform, as configured in the previous step.

### Required Information

| Item | Description |
|------|-------------|
| Instance GUID | The GUID of the Flow instance |
| Bootstrap Port | The configured Flow Bootstrap communications port (default: 4501) |
| Main Platform Address | IP Address or hostname of the main platform (hostname requires DNS) |

### Platforms.settings File Format

Create a `Platforms.settings` file with the following JSON object:

```json
[
  {
    "remote": "true",
    "properties": {
      "Name": "Remote Platform",
      "Uri": "http://12.345.34.56:4501/flow-software/flow/instances/8B5E4CD0-EC3E-4B27-83EF-0DF96D41B475/platform"
    }
  }
]
```

**Important:** Replace the following values:
- `Name` - The name of your remote platform as configured in the Config Tool
- `Uri` - The correct IP address, port, and instance GUID

### File Location

| Platform | Path |
|----------|------|
| **Windows** | `C:\ProgramData\Flow Software\Flow\Bootstrap` |
| **Linux** | `/var/lib/Flow Software/Flow/Bootstrap` |
| **Docker** | `/var/lib/Flow Software/Flow/Bootstrap` |

---

## Deployment

After configuring the `Platforms.settings` file, the remote platform can be deployed from the Config Tool and a data source can be associated with the platform.

---

## ProveIT Edge Stack Notes

For remote platform scenarios in the ProveIT Edge Stack:

### Use Cases

- **Edge-to-Cloud**: Edge devices that cannot directly access the central SQL database
- **Multi-Site Deployments**: Sites connected via VPN with limited SQL access
- **Air-Gapped Networks**: OT networks that need to push data to IT systems

### Example Configuration

For a remote platform connecting to the main analytics platform:

```json
[
  {
    "remote": "true",
    "properties": {
      "Name": "Edge-Remote-Platform",
      "Uri": "http://192.168.30.231:4501/flow-software/flow/instances/{INSTANCE-GUID}/platform"
    }
  }
]
```

Replace `{INSTANCE-GUID}` with the actual Flow instance GUID from your deployment.

### Docker Volume Mount

If running the remote Bootstrap in Docker, mount the settings file:

```yaml
volumes:
  - ./config/flow/Platforms.settings:/var/lib/Flow Software/Flow/Bootstrap/Platforms.settings:ro
```

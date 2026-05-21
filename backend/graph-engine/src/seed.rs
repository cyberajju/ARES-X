/// Demo data seeder for the graph engine.
///
/// Creates a realistic sample infrastructure graph with approximately
/// 20 nodes and 30 edges representing a typical enterprise network.

use crate::graph::store::InfraGraph;
use crate::graph::types::{Edge, EdgeType, Node, NodeId, NodeType};

/// Seed the graph with sample infrastructure data for demonstration.
///
/// Creates a realistic topology including:
/// - 3 servers (web, app, mail)
/// - 2 databases (primary, replica)
/// - 2 firewalls (external, internal)
/// - 3 applications (CRM, ERP, monitoring)
/// - 2 load balancers (external, internal)
/// - 2 workstations (dev, admin)
/// - 2 cloud VMs (ci/cd, staging)
/// - 2 identities (admin account, service account)
/// - 1 OT controller (SCADA)
/// - 1 OT sensor (temperature)
pub fn seed_demo_graph() -> InfraGraph {
    let mut graph = InfraGraph::new();

    // --- Nodes ---

    // Firewalls (high criticality)
    let _ = graph.add_node(
        Node::new(NodeId::new("fw-ext"), NodeType::Firewall, "External Firewall", 0.95)
            .with_description("Perimeter firewall protecting DMZ")
            .with_property("vendor", "Palo Alto")
            .with_property("zone", "dmz")
            .with_tag("perimeter"),
    );
    let _ = graph.add_node(
        Node::new(NodeId::new("fw-int"), NodeType::Firewall, "Internal Firewall", 0.90)
            .with_description("Internal segmentation firewall")
            .with_property("vendor", "Fortinet")
            .with_property("zone", "internal")
            .with_tag("segmentation"),
    );

    // Load Balancers
    let _ = graph.add_node(
        Node::new(NodeId::new("lb-ext"), NodeType::LoadBalancer, "External LB", 0.80)
            .with_description("External-facing load balancer")
            .with_property("type", "L7")
            .with_property("zone", "dmz"),
    );
    let _ = graph.add_node(
        Node::new(NodeId::new("lb-int"), NodeType::LoadBalancer, "Internal LB", 0.75)
            .with_description("Internal service load balancer")
            .with_property("type", "L4")
            .with_property("zone", "internal"),
    );

    // Servers
    let _ = graph.add_node(
        Node::new(NodeId::new("srv-web"), NodeType::Server, "Web Server", 0.70)
            .with_description("Public-facing web server")
            .with_property("os", "Ubuntu 22.04")
            .with_property("zone", "dmz")
            .with_tag("public"),
    );
    let _ = graph.add_node(
        Node::new(NodeId::new("srv-app"), NodeType::Server, "Application Server", 0.80)
            .with_description("Core application server")
            .with_property("os", "RHEL 9")
            .with_property("zone", "internal")
            .with_tag("core"),
    );
    let _ = graph.add_node(
        Node::new(NodeId::new("srv-mail"), NodeType::Server, "Mail Server", 0.65)
            .with_description("Corporate email server")
            .with_property("os", "Windows Server 2022")
            .with_property("zone", "internal"),
    );

    // Databases (high criticality)
    let _ = graph.add_node(
        Node::new(NodeId::new("db-primary"), NodeType::Database, "Primary Database", 0.95)
            .with_description("Primary PostgreSQL database")
            .with_property("engine", "PostgreSQL 15")
            .with_property("zone", "data")
            .with_tag("pii")
            .with_tag("critical"),
    );
    let _ = graph.add_node(
        Node::new(NodeId::new("db-replica"), NodeType::Database, "Replica Database", 0.80)
            .with_description("Read replica for reporting")
            .with_property("engine", "PostgreSQL 15")
            .with_property("zone", "data")
            .with_tag("replica"),
    );

    // Applications
    let _ = graph.add_node(
        Node::new(NodeId::new("app-crm"), NodeType::Application, "CRM Application", 0.70)
            .with_description("Customer relationship management")
            .with_property("framework", "Java Spring")
            .with_tag("business-critical"),
    );
    let _ = graph.add_node(
        Node::new(NodeId::new("app-erp"), NodeType::Application, "ERP System", 0.85)
            .with_description("Enterprise resource planning")
            .with_property("framework", "SAP")
            .with_tag("business-critical"),
    );
    let _ = graph.add_node(
        Node::new(NodeId::new("app-monitor"), NodeType::Application, "Monitoring", 0.60)
            .with_description("Infrastructure monitoring platform")
            .with_property("framework", "Grafana"),
    );

    // Workstations (lower criticality)
    let _ = graph.add_node(
        Node::new(NodeId::new("ws-dev"), NodeType::Workstation, "Developer Workstation", 0.30)
            .with_description("Software developer machine")
            .with_property("os", "macOS")
            .with_tag("endpoint"),
    );
    let _ = graph.add_node(
        Node::new(NodeId::new("ws-admin"), NodeType::Workstation, "Admin Workstation", 0.50)
            .with_description("System administrator workstation")
            .with_property("os", "Windows 11")
            .with_tag("endpoint")
            .with_tag("privileged"),
    );

    // Cloud VMs
    let _ = graph.add_node(
        Node::new(NodeId::new("vm-cicd"), NodeType::CloudVM, "CI/CD Pipeline", 0.65)
            .with_description("Continuous integration and deployment")
            .with_property("provider", "AWS")
            .with_property("instance", "m5.xlarge"),
    );
    let _ = graph.add_node(
        Node::new(NodeId::new("vm-staging"), NodeType::CloudVM, "Staging Environment", 0.40)
            .with_description("Pre-production staging")
            .with_property("provider", "AWS")
            .with_property("instance", "t3.large"),
    );

    // Identities
    let _ = graph.add_node(
        Node::new(NodeId::new("id-admin"), NodeType::Identity, "Admin Account", 0.90)
            .with_description("Domain administrator account")
            .with_property("type", "privileged")
            .with_tag("high-privilege"),
    );
    let _ = graph.add_node(
        Node::new(NodeId::new("id-svc"), NodeType::Identity, "Service Account", 0.70)
            .with_description("Application service account")
            .with_property("type", "service")
            .with_tag("automated"),
    );

    // OT devices
    let _ = graph.add_node(
        Node::new(NodeId::new("ot-scada"), NodeType::OTController, "SCADA Controller", 0.95)
            .with_description("Industrial control system")
            .with_property("protocol", "Modbus")
            .with_property("zone", "ot")
            .with_tag("critical-infrastructure"),
    );
    let _ = graph.add_node(
        Node::new(NodeId::new("ot-sensor"), NodeType::OTSensor, "Temperature Sensor", 0.40)
            .with_description("Environmental monitoring sensor")
            .with_property("protocol", "BACnet")
            .with_property("zone", "ot"),
    );

    // --- Edges ---

    // External traffic flow: internet -> fw-ext -> lb-ext -> srv-web
    let _ = graph.add_edge(
        Edge::new("e-01", "fw-ext", "lb-ext", EdgeType::RoutesTo, 0.9),
    );
    let _ = graph.add_edge(
        Edge::new("e-02", "lb-ext", "srv-web", EdgeType::RoutesTo, 0.9),
    );

    // Web server connects to app server
    let _ = graph.add_edge(
        Edge::new("e-03", "srv-web", "srv-app", EdgeType::ConnectsTo, 0.8),
    );

    // Internal LB routes to app server
    let _ = graph.add_edge(
        Edge::new("e-04", "fw-int", "lb-int", EdgeType::RoutesTo, 0.85),
    );
    let _ = graph.add_edge(
        Edge::new("e-05", "lb-int", "srv-app", EdgeType::RoutesTo, 0.85),
    );

    // App server depends on databases
    let _ = graph.add_edge(
        Edge::new("e-06", "srv-app", "db-primary", EdgeType::DependsOn, 0.95),
    );
    let _ = graph.add_edge(
        Edge::new("e-07", "db-primary", "db-replica", EdgeType::ReplicatesTo, 0.9),
    );

    // Applications depend on app server
    let _ = graph.add_edge(
        Edge::new("e-08", "app-crm", "srv-app", EdgeType::DependsOn, 0.8),
    );
    let _ = graph.add_edge(
        Edge::new("e-09", "app-erp", "srv-app", EdgeType::DependsOn, 0.85),
    );
    let _ = graph.add_edge(
        Edge::new("e-10", "app-erp", "db-primary", EdgeType::DependsOn, 0.9),
    );

    // Monitoring observes servers
    let _ = graph.add_edge(
        Edge::new("e-11", "app-monitor", "srv-web", EdgeType::Monitors, 0.7),
    );
    let _ = graph.add_edge(
        Edge::new("e-12", "app-monitor", "srv-app", EdgeType::Monitors, 0.7),
    );
    let _ = graph.add_edge(
        Edge::new("e-13", "app-monitor", "db-primary", EdgeType::Monitors, 0.7),
    );

    // Workstations access through firewall
    let _ = graph.add_edge(
        Edge::new("e-14", "ws-dev", "fw-int", EdgeType::AccessibleFrom, 0.6),
    );
    let _ = graph.add_edge(
        Edge::new("e-15", "ws-admin", "fw-int", EdgeType::AccessibleFrom, 0.7),
    );

    // Admin workstation authenticates to admin identity
    let _ = graph.add_edge(
        Edge::new("e-16", "ws-admin", "id-admin", EdgeType::AuthenticatesTo, 0.8),
    );

    // Admin identity has access to servers
    let _ = graph.add_edge(
        Edge::new("e-17", "id-admin", "srv-app", EdgeType::AccessibleFrom, 0.9),
    );
    let _ = graph.add_edge(
        Edge::new("e-18", "id-admin", "srv-web", EdgeType::AccessibleFrom, 0.9),
    );
    let _ = graph.add_edge(
        Edge::new("e-19", "id-admin", "db-primary", EdgeType::AccessibleFrom, 0.85),
    );

    // Service account used by CI/CD
    let _ = graph.add_edge(
        Edge::new("e-20", "vm-cicd", "id-svc", EdgeType::AuthenticatesTo, 0.75),
    );
    let _ = graph.add_edge(
        Edge::new("e-21", "id-svc", "vm-staging", EdgeType::AccessibleFrom, 0.8),
    );
    let _ = graph.add_edge(
        Edge::new("e-22", "id-svc", "srv-app", EdgeType::AccessibleFrom, 0.7),
    );

    // CI/CD deploys to staging
    let _ = graph.add_edge(
        Edge::new("e-23", "vm-cicd", "vm-staging", EdgeType::ConnectsTo, 0.8),
    );

    // Mail server connections
    let _ = graph.add_edge(
        Edge::new("e-24", "srv-mail", "fw-ext", EdgeType::ConnectsTo, 0.7),
    );
    let _ = graph.add_edge(
        Edge::new("e-25", "srv-mail", "id-admin", EdgeType::DependsOn, 0.5),
    );

    // OT network: controller manages sensor, accessible from internal
    let _ = graph.add_edge(
        Edge::new("e-26", "ot-scada", "ot-sensor", EdgeType::Controls, 0.9),
    );
    let _ = graph.add_edge(
        Edge::new("e-27", "fw-int", "ot-scada", EdgeType::RoutesTo, 0.4),
    );

    // Database backup
    let _ = graph.add_edge(
        Edge::new("e-28", "db-primary", "vm-cicd", EdgeType::BacksUp, 0.6),
    );

    // Developer workstation to CI/CD
    let _ = graph.add_edge(
        Edge::new("e-29", "ws-dev", "vm-cicd", EdgeType::ConnectsTo, 0.7),
    );

    // LB-ext depends on fw-ext for protection
    let _ = graph.add_edge(
        Edge::new("e-30", "lb-ext", "fw-ext", EdgeType::DependsOn, 0.85),
    );

    graph
}
